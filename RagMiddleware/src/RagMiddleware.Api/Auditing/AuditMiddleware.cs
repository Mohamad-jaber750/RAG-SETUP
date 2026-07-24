using System.Diagnostics;
using System.Security.Claims;
using RagMiddleware.Application.Auditing;

namespace RagMiddleware.Api.Auditing;

public sealed class AuditMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<AuditMiddleware> _logger;

    public AuditMiddleware(RequestDelegate next, ILogger<AuditMiddleware> logger)
    {
        _next = next;
        _logger = logger;
    }

    public async Task InvokeAsync(HttpContext context, IAuditLogService auditLogService)
    {
        var path = context.Request.Path.Value ?? string.Empty;
        var shouldAudit = path.StartsWith("/api/rag", StringComparison.OrdinalIgnoreCase)
            || path.StartsWith("/api/chat", StringComparison.OrdinalIgnoreCase)
            || path.StartsWith("/api/conversations", StringComparison.OrdinalIgnoreCase)
            || path.StartsWith("/api/auth", StringComparison.OrdinalIgnoreCase);

        if (!shouldAudit)
        {
            await _next(context);
            return;
        }

        var stopwatch = Stopwatch.StartNew();
        await _next(context);
        stopwatch.Stop();

        Guid? userId = Guid.TryParse(context.User.FindFirstValue(ClaimTypes.NameIdentifier), out var parsedUserId)
            ? parsedUserId
            : null;

        try
        {
            await auditLogService.WriteAsync(new AuditLogEntry(
                userId,
                ToAction(context.Request.Method, path, context.Response.StatusCode),
                path,
                BuildSummary(context),
                context.Response.StatusCode,
                context.Connection.RemoteIpAddress?.ToString(),
                stopwatch.ElapsedMilliseconds), CancellationToken.None);
        }
        catch (Exception exception)
        {
            _logger.LogError(exception, "Could not persist audit log for {Method} {Path}.",
                context.Request.Method, path);
        }
    }

    private static string ToAction(string method, string path, int statusCode)
    {
        if (path.Contains("/auth", StringComparison.OrdinalIgnoreCase))
        {
            return statusCode is >= 200 and < 400 ? "AUTH_EVENT" : "AUTH_FAILED";
        }

        if (path.Contains("/chat", StringComparison.OrdinalIgnoreCase))
        {
            return "RAG_QUERY";
        }

        if (path.Contains("/conversations", StringComparison.OrdinalIgnoreCase))
        {
            return $"{method}_CONVERSATION";
        }

        return $"{method}_RAG_REQUEST";
    }

    private static string BuildSummary(HttpContext context)
    {
        return $"{context.Request.Method} {context.Request.Path}";
    }
}
