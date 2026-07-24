using System.Net.Http.Headers;

namespace RagMiddleware.Application.Rag;

public interface IRagApiClient
{
    Task<HttpResponseMessage> StreamChatAsync(ChatRequest request, CancellationToken cancellationToken);
    Task<HttpResponseMessage> SendAsync(HttpMethod method, string path, HttpContent? content, MediaTypeHeaderValue? accept, CancellationToken cancellationToken);
}
