using MongoDB.Bson;
using MongoDB.Bson.Serialization.Attributes;

namespace RagMiddleware.Domain.Entities;

public sealed class AuditLog
{
    [BsonId]
    [BsonRepresentation(BsonType.String)]
    public Guid Id { get; set; } = Guid.NewGuid();

    [BsonGuidRepresentation(GuidRepresentation.Standard)]
    public Guid? UserId { get; set; }
    public string Action { get; set; } = string.Empty;
    public string Endpoint { get; set; } = string.Empty;
    public string? RequestSummary { get; set; }
    public int StatusCode { get; set; }
    public string? IpAddress { get; set; }
    public DateTimeOffset Timestamp { get; set; } = DateTimeOffset.UtcNow;
    public long DurationMs { get; set; }
}
