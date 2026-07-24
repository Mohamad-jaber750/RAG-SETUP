using Microsoft.Extensions.Options;
using MongoDB.Driver;
using RagMiddleware.Application.Options;
using RagMiddleware.Domain.Entities;

namespace RagMiddleware.Infrastructure.Persistence;

public sealed class MongoDbContext
{
    public MongoDbContext(IOptions<MongoDbOptions> options)
    {
        var client = new MongoClient(options.Value.ConnectionString);
        Database = client.GetDatabase(options.Value.DatabaseName);
    }

    public IMongoDatabase Database { get; }
    public IMongoCollection<ApplicationUser> Users => Database.GetCollection<ApplicationUser>("users");
    public IMongoCollection<AuditLog> AuditLogs => Database.GetCollection<AuditLog>("audit_logs");

    public async Task EnsureIndexesAsync(CancellationToken cancellationToken)
    {
        await Users.Indexes.CreateOneAsync(
            new CreateIndexModel<ApplicationUser>(
                Builders<ApplicationUser>.IndexKeys.Ascending(user => user.GoogleSubject),
                new CreateIndexOptions { Unique = true, Sparse = true }),
            cancellationToken: cancellationToken);

        await Users.Indexes.CreateOneAsync(
            new CreateIndexModel<ApplicationUser>(
                Builders<ApplicationUser>.IndexKeys.Ascending(user => user.Email),
                new CreateIndexOptions { Unique = true }),
            cancellationToken: cancellationToken);

        await AuditLogs.Indexes.CreateManyAsync(
            [
                new CreateIndexModel<AuditLog>(Builders<AuditLog>.IndexKeys.Descending(log => log.Timestamp)),
                new CreateIndexModel<AuditLog>(Builders<AuditLog>.IndexKeys.Ascending(log => log.Action))
            ],
            cancellationToken);
    }
}
