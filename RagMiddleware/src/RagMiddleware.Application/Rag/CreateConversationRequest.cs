using System.Text.Json.Serialization;

namespace RagMiddleware.Application.Rag;

public sealed class CreateConversationRequest
{
    [JsonPropertyName("title")]
    public string? Title { get; init; }
}
