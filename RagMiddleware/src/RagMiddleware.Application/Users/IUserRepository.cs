using RagMiddleware.Domain.Entities;

namespace RagMiddleware.Application.Users;

public interface IUserRepository
{
    Task<ApplicationUser?> FindByIdAsync(Guid id, CancellationToken cancellationToken);
    Task<ApplicationUser?> FindByEmailAsync(string email, CancellationToken cancellationToken);
    Task<ApplicationUser?> FindByGoogleSubjectAsync(string googleSubject, CancellationToken cancellationToken);
    Task<ApplicationUser> UpsertGoogleUserAsync(string googleSubject, string email, string? displayName, string? avatarUrl, CancellationToken cancellationToken);
}
