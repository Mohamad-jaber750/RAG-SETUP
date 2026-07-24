using System.Security.Claims;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Authentication.Cookies;
using Microsoft.AspNetCore.Authentication.Google;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using RagMiddleware.Api.Security;
using RagMiddleware.Application.Users;

namespace RagMiddleware.Api.Controllers;

[ApiController]
[Route("api/auth")]
public sealed class AuthController : ControllerBase
{
    private readonly IUserRepository _userRepository;
    private readonly TokenService _tokenService;
    private readonly IConfiguration _configuration;

    public AuthController(
        IUserRepository userRepository,
        TokenService tokenService,
        IConfiguration configuration)
    {
        _userRepository = userRepository;
        _tokenService = tokenService;
        _configuration = configuration;
    }

    [HttpGet("login/google")]
    [AllowAnonymous]
    public IActionResult LoginWithGoogle([FromQuery] string? returnUrl = null)
    {
        var clientId = _configuration["Authentication:Google:ClientId"];
        var clientSecret = _configuration["Authentication:Google:ClientSecret"];
        if (string.IsNullOrWhiteSpace(clientId) || string.IsNullOrWhiteSpace(clientSecret))
        {
            const string message =
                "Google sign-in is not configured. Add the Google ClientId and ClientSecret to RagMiddleware user secrets.";

            if (TryGetLocalReturnUrl(returnUrl, out var safeReturnUrl))
            {
                var separator = safeReturnUrl.Contains('?') ? '&' : '?';
                return Redirect($"{safeReturnUrl}{separator}auth_error={Uri.EscapeDataString(message)}");
            }

            return Problem(
                statusCode: StatusCodes.Status503ServiceUnavailable,
                title: "Google sign-in is not configured",
                detail: message);
        }

        var properties = new AuthenticationProperties
        {
            RedirectUri = Url.Action(nameof(GoogleCallback), new { returnUrl })
        };

        return Challenge(properties, GoogleDefaults.AuthenticationScheme);
    }

    [HttpGet("google/callback")]
    [AllowAnonymous]
    public async Task<IActionResult> GoogleCallback([FromQuery] string? returnUrl = null)
    {
        var result = await HttpContext.AuthenticateAsync(
            CookieAuthenticationDefaults.AuthenticationScheme);
        if (!result.Succeeded || result.Principal is null)
        {
            return Unauthorized(new { error = "Google sign-in failed." });
        }

        var googleSubject = result.Principal.FindFirstValue(ClaimTypes.NameIdentifier);
        var email = result.Principal.FindFirstValue(ClaimTypes.Email);
        if (string.IsNullOrWhiteSpace(googleSubject) || string.IsNullOrWhiteSpace(email))
        {
            return Unauthorized(new { error = "Google profile did not include required identity fields." });
        }

        var user = await _userRepository.UpsertGoogleUserAsync(
            googleSubject,
            email,
            result.Principal.FindFirstValue(ClaimTypes.Name),
            result.Principal.FindFirstValue("picture"),
            HttpContext.RequestAborted);

        var accessToken = _tokenService.CreateAccessToken(user);

        if (TryGetLocalReturnUrl(returnUrl, out var safeReturnUrl))
        {
            Response.Cookies.Append("rag_access_token", accessToken, new CookieOptions
            {
                HttpOnly = true,
                Secure = Request.IsHttps,
                SameSite = SameSiteMode.Lax,
                Expires = DateTimeOffset.UtcNow.AddHours(1),
                IsEssential = true
            });
            return Redirect(safeReturnUrl);
        }

        return Ok(new { access_token = accessToken, token_type = "Bearer" });
    }

    [HttpGet("me")]
    [Authorize]
    public async Task<IActionResult> Me()
    {
        var userIdValue = User.FindFirstValue(ClaimTypes.NameIdentifier);
        if (!Guid.TryParse(userIdValue, out var userId))
        {
            return Unauthorized();
        }

        var user = await _userRepository.FindByIdAsync(userId, HttpContext.RequestAborted);
        if (user is null)
        {
            return Unauthorized();
        }

        return Ok(new { id = user.Id, user.Email, user.DisplayName, user.AvatarUrl });
    }

    [HttpPost("logout")]
    [Authorize]
    public IActionResult Logout()
    {
        Response.Cookies.Delete("rag_access_token");
        return Ok(new { logged_out = true });
    }

    private static bool TryGetLocalReturnUrl(string? returnUrl, out string safeReturnUrl)
    {
        safeReturnUrl = string.Empty;
        if (!Uri.TryCreate(returnUrl, UriKind.Absolute, out var uri))
        {
            return false;
        }

        if (uri.Scheme is not ("http" or "https")
            || uri.Host is not ("localhost" or "127.0.0.1"))
        {
            return false;
        }

        safeReturnUrl = uri.ToString();
        return true;
    }
}
