using System.Net.Http.Headers;
using System.Net.Http.Json;
using Microsoft.Extensions.Options;
using RagMiddleware.Application.Options;
using RagMiddleware.Application.Rag;

namespace RagMiddleware.Infrastructure.Rag;

public sealed class RagApiClient : IRagApiClient
{
    private readonly HttpClient _httpClient;
    private readonly RagApiOptions _options;

    public RagApiClient(HttpClient httpClient, IOptions<RagApiOptions> options)
    {
        _httpClient = httpClient;
        _options = options.Value;
    }

    public Task<HttpResponseMessage> StreamChatAsync(ChatRequest request, CancellationToken cancellationToken)
    {
        return SendAsync(
            HttpMethod.Post,
            "/api/chat/stream",
            JsonContent.Create(request),
            new MediaTypeHeaderValue("text/event-stream"),
            cancellationToken);
    }

    public async Task<HttpResponseMessage> SendAsync(HttpMethod method, string path, HttpContent? content, MediaTypeHeaderValue? accept, CancellationToken cancellationToken)
    {
        // Python's BaseHTTPRequestHandler does not decode chunked request bodies.
        // Buffer JSON first so HttpClient sends an explicit Content-Length.
        if (content is not null)
        {
            await content.LoadIntoBufferAsync();
        }

        using var request = new HttpRequestMessage(method, path) { Content = content };

        if (!string.IsNullOrWhiteSpace(_options.BearerToken))
        {
            request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", _options.BearerToken);
        }
        else if (!string.IsNullOrWhiteSpace(_options.ApiKey))
        {
            request.Headers.Add("X-API-Key", _options.ApiKey);
        }

        if (accept is not null)
        {
            request.Headers.Accept.Add(new MediaTypeWithQualityHeaderValue(accept.MediaType ?? "application/json"));
        }

        return await _httpClient.SendAsync(request, HttpCompletionOption.ResponseHeadersRead, cancellationToken);
    }
}
