using System.Net.Http.Headers;
using System.Net.Http.Json;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using RagMiddleware.Application.Rag;

namespace RagMiddleware.Api.Controllers;

[ApiController]
[Authorize]
[Route("api")]
public sealed class RagController : ControllerBase
{
    private readonly IRagApiClient _ragApiClient;
    private readonly ILogger<RagController> _logger;

    public RagController(IRagApiClient ragApiClient, ILogger<RagController> logger)
    {
        _ragApiClient = ragApiClient;
        _logger = logger;
    }

    [HttpPost("chat")]
    public async Task<IActionResult> Chat(ChatRequest request, CancellationToken cancellationToken)
    {
        using var response = await _ragApiClient.SendAsync(HttpMethod.Post, "/api/chat", JsonContent.Create(request), null, cancellationToken);
        return await ToSanitizedResult(response, cancellationToken);
    }

    [HttpPost("chat/stream")]
    public async Task StreamChat(ChatRequest request, CancellationToken cancellationToken)
    {
        using var upstreamResponse = await _ragApiClient.StreamChatAsync(request, cancellationToken);
        if (!upstreamResponse.IsSuccessStatusCode)
        {
            var upstreamBody = await upstreamResponse.Content.ReadAsStringAsync(cancellationToken);
            _logger.LogWarning("RAG stream failed with status {StatusCode}: {Body}",
                (int)upstreamResponse.StatusCode, upstreamBody);
            Response.StatusCode = (int)upstreamResponse.StatusCode;
            await Response.WriteAsJsonAsync(
                new { error = "The RAG service could not complete the streaming request." },
                cancellationToken);
            return;
        }

        Response.ContentType = "text/event-stream; charset=utf-8";
        await using var stream = await upstreamResponse.Content.ReadAsStreamAsync(cancellationToken);
        await stream.CopyToAsync(Response.Body, cancellationToken);
    }

    [HttpGet("conversations")]
    public async Task<IActionResult> ListConversations(CancellationToken cancellationToken)
    {
        using var response = await _ragApiClient.SendAsync(HttpMethod.Get, "/api/conversations", null, null, cancellationToken);
        return await ToSanitizedResult(response, cancellationToken);
    }

    [HttpPost("conversations")]
    public async Task<IActionResult> CreateConversation(CreateConversationRequest request, CancellationToken cancellationToken)
    {
        using var response = await _ragApiClient.SendAsync(HttpMethod.Post, "/api/conversations", JsonContent.Create(request), null, cancellationToken);
        return await ToSanitizedResult(response, cancellationToken);
    }

    [HttpGet("conversations/{id}")]
    public async Task<IActionResult> GetConversation(string id, CancellationToken cancellationToken)
    {
        using var response = await _ragApiClient.SendAsync(HttpMethod.Get, $"/api/conversations/{Uri.EscapeDataString(id)}", null, null, cancellationToken);
        return await ToSanitizedResult(response, cancellationToken);
    }

    [HttpDelete("conversations/{id}")]
    public async Task<IActionResult> DeleteConversation(string id, CancellationToken cancellationToken)
    {
        using var response = await _ragApiClient.SendAsync(HttpMethod.Delete, $"/api/conversations/{Uri.EscapeDataString(id)}", null, null, cancellationToken);
        return await ToSanitizedResult(response, cancellationToken);
    }

    [HttpPost("conversations/{conversationId}/messages/{messageId}/regenerate")]
    public async Task Regenerate(string conversationId, string messageId, CancellationToken cancellationToken)
    {
        var path = $"/api/conversations/{Uri.EscapeDataString(conversationId)}/messages/{Uri.EscapeDataString(messageId)}/regenerate";
        using var upstreamResponse = await _ragApiClient.SendAsync(HttpMethod.Post, path, JsonContent.Create(new { }), null, cancellationToken);
        Response.StatusCode = (int)upstreamResponse.StatusCode;
        Response.ContentType = upstreamResponse.Content.Headers.ContentType?.ToString() ?? "text/event-stream; charset=utf-8";
        await using var stream = await upstreamResponse.Content.ReadAsStreamAsync(cancellationToken);
        await stream.CopyToAsync(Response.Body, cancellationToken);
    }

    [HttpPost("conversations/{conversationId}/messages/{messageId}/feedback")]
    public async Task<IActionResult> Feedback(string conversationId, string messageId, [FromBody] object feedback, CancellationToken cancellationToken)
    {
        var path = $"/api/conversations/{Uri.EscapeDataString(conversationId)}/messages/{Uri.EscapeDataString(messageId)}/feedback";
        using var response = await _ragApiClient.SendAsync(HttpMethod.Post, path, JsonContent.Create(feedback), null, cancellationToken);
        return await ToSanitizedResult(response, cancellationToken);
    }

    private async Task<IActionResult> ToSanitizedResult(HttpResponseMessage response, CancellationToken cancellationToken)
    {
        var contentType = response.Content.Headers.ContentType?.ToString() ?? "application/json; charset=utf-8";
        var body = await response.Content.ReadAsStringAsync(cancellationToken);

        if (!response.IsSuccessStatusCode)
        {
            _logger.LogWarning("RAG API failed with status {StatusCode}: {Body}", (int)response.StatusCode, body);
            return StatusCode((int)response.StatusCode, new { error = "The RAG service could not complete the request." });
        }

        return Content(body, contentType);
    }
}
