using MongoDB.Driver;
using RagMiddleware.Application.Users;
using RagMiddleware.Domain.Entities;
using RagMiddleware.Infrastructure.Persistence;

namespace RagMiddleware.Infrastructure.Users;

public sealed class MongoUserRepository : IUserRepository
{
    private readonly MongoDbContext _context;

    public MongoUserRepository(MongoDbContext context)
    {
        _context = context;
    }

    public async Task<ApplicationUser?> FindByIdAsync(Guid id, CancellationToken cancellationToken)
    {
        return await _context.Users.Find(user => user.Id == id).SingleOrDefaultAsync(cancellationToken);
    }

    public async Task<ApplicationUser?> FindByEmailAsync(string email, CancellationToken cancellationToken)
    {
        return await _context.Users.Find(user => user.Email == email).SingleOrDefaultAsync(cancellationToken);
    }

    public async Task<ApplicationUser?> FindByGoogleSubjectAsync(string googleSubject, CancellationToken cancellationToken)
    {
        return await _context.Users.Find(user => user.GoogleSubject == googleSubject).SingleOrDefaultAsync(cancellationToken);
    }

    public async Task<ApplicationUser> UpsertGoogleUserAsync(string googleSubject, string email, string? displayName, string? avatarUrl, CancellationToken cancellationToken)
    {
        var existingUser = await FindByGoogleSubjectAsync(googleSubject, cancellationToken)
            ?? await FindByEmailAsync(email, cancellationToken);

        if (existingUser is null)
        {
            existingUser = new ApplicationUser
            {
                Email = email,
                GoogleSubject = googleSubject,
                DisplayName = displayName,
                AvatarUrl = avatarUrl
            };
        }
        else
        {
            existingUser.GoogleSubject = googleSubject;
            existingUser.DisplayName = displayName ?? existingUser.DisplayName;
            existingUser.AvatarUrl = avatarUrl ?? existingUser.AvatarUrl;
        }

        await _context.Users.ReplaceOneAsync(
            user => user.Id == existingUser.Id,
            existingUser,
            new ReplaceOptions { IsUpsert = true },
            cancellationToken);

        return existingUser;
    }
}
