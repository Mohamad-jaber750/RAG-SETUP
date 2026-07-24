using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using MongoDB.Driver;
using RagMiddleware.Infrastructure.Persistence;

namespace RagMiddleware.Api.Controllers;

[ApiController]
[Authorize(Roles = "Admin")]
[Route("api/admin/audit-logs")]
public sealed class AdminAuditLogsController : ControllerBase
{
    [HttpGet]
    public async Task<IActionResult> Get(
        MongoDbContext dbContext,
        [FromQuery] string? action,
        [FromQuery] DateTimeOffset? from,
        [FromQuery] DateTimeOffset? to,
        [FromQuery] int page = 1,
        [FromQuery] int pageSize = 50,
        CancellationToken cancellationToken = default)
    {
        page = Math.Max(page, 1);
        pageSize = Math.Clamp(pageSize, 1, 200);

        var filters = new List<FilterDefinition<RagMiddleware.Domain.Entities.AuditLog>>();
        if (!string.IsNullOrWhiteSpace(action))
        {
            filters.Add(Builders<RagMiddleware.Domain.Entities.AuditLog>.Filter.Eq(log => log.Action, action));
        }

        if (from is not null)
        {
            filters.Add(Builders<RagMiddleware.Domain.Entities.AuditLog>.Filter.Gte(log => log.Timestamp, from.Value));
        }

        if (to is not null)
        {
            filters.Add(Builders<RagMiddleware.Domain.Entities.AuditLog>.Filter.Lte(log => log.Timestamp, to.Value));
        }

        var filter = filters.Count == 0
            ? Builders<RagMiddleware.Domain.Entities.AuditLog>.Filter.Empty
            : Builders<RagMiddleware.Domain.Entities.AuditLog>.Filter.And(filters);

        var total = await dbContext.AuditLogs.CountDocumentsAsync(filter, cancellationToken: cancellationToken);
        var items = await dbContext.AuditLogs
            .Find(filter)
            .SortByDescending(log => log.Timestamp)
            .Skip((page - 1) * pageSize)
            .Limit(pageSize)
            .ToListAsync(cancellationToken);

        return Ok(new { total, page, pageSize, items });
    }
}
