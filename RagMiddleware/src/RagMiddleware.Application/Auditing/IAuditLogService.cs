namespace RagMiddleware.Application.Auditing;

public interface IAuditLogService
{
    Task WriteAsync(AuditLogEntry entry, CancellationToken cancellationToken);
}
