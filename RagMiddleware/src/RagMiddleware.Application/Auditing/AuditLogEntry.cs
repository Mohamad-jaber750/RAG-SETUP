namespace RagMiddleware.Application.Auditing;

public sealed record AuditLogEntry(
    Guid? UserId,
    string Action,
    string Endpoint,
    string? RequestSummary,
    int StatusCode,
    string? IpAddress,
    long DurationMs);
