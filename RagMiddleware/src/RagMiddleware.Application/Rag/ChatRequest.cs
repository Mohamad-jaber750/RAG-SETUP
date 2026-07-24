using System.ComponentModel.DataAnnotations;
using System.Text.Json.Serialization;

namespace RagMiddleware.Application.Rag;

public sealed class ChatRequest
{
    [Required]
    [MaxLength(4000)]
    [JsonPropertyName("question")]
    public string Question { get; init; } = string.Empty;

    [JsonPropertyName("conversation_id")]
    public string? ConversationId { get; init; }
}
