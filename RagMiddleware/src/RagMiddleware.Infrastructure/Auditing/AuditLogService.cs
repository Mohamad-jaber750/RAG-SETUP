using RagMiddleware.Application.Auditing;
using RagMiddleware.Domain.Entities;
using RagMiddleware.Infrastructure.Persistence;

namespace RagMiddleware.Infrastructure.Auditing;

public sealed class AuditLogService : IAuditLogService
{
    private readonly MongoDbContext _context;

    public AuditLogService(MongoDbContext context)
    {
        _context = context;
    }

    public async Task WriteAsync(AuditLogEntry entry, CancellationToken cancellationToken)
    {
        var auditLog = new AuditLog
        {
            UserId = entry.UserId,
            Action = entry.Action,
            Endpoint = entry.Endpoint,
            RequestSummary = entry.RequestSummary,
            StatusCode = entry.StatusCode,
            IpAddress = entry.IpAddress,
            DurationMs = entry.DurationMs
        };

        await _context.AuditLogs.InsertOneAsync(auditLog, cancellationToken: cancellationToken);
    }
}
