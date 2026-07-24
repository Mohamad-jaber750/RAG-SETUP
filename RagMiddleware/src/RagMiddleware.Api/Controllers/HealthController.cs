using Microsoft.AspNetCore.Mvc;
using MongoDB.Driver;
using RagMiddleware.Infrastructure.Persistence;

namespace RagMiddleware.Api.Controllers;

[ApiController]
[Route("")]
public sealed class HealthController : ControllerBase
{
    [HttpGet("health")]
    [HttpGet("api/health")]
    public async Task<IActionResult> Get(MongoDbContext dbContext, CancellationToken cancellationToken)
    {
        var database = "connected";
        try
        {
            await dbContext.Database.RunCommandAsync(
                new JsonCommand<MongoDB.Bson.BsonDocument>("{ ping: 1 }"),
                cancellationToken: cancellationToken);
        }
        catch
        {
            database = "unavailable";
        }

        return Ok(new { status = "ok", database });
    }
}
