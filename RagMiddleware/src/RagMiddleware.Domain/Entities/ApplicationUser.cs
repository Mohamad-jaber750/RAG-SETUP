using MongoDB.Bson;
using MongoDB.Bson.Serialization.Attributes;

namespace RagMiddleware.Domain.Entities;

public sealed class ApplicationUser
{
    [BsonId]
    [BsonRepresentation(BsonType.String)]
    public Guid Id { get; set; } = Guid.NewGuid();

    public string Email { get; set; } = string.Empty;
    public string? GoogleSubject { get; set; }
    public string? DisplayName { get; set; }
    public string? AvatarUrl { get; set; }
    public List<string> Roles { get; set; } = [];
    public DateTimeOffset CreatedAt { get; set; } = DateTimeOffset.UtcNow;
}
