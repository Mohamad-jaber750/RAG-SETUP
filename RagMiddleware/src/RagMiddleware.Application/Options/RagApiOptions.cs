using System.ComponentModel.DataAnnotations;

namespace RagMiddleware.Application.Options;

public sealed class RagApiOptions
{
    public const string SectionName = "RagApi";

    [Required]
    public string BaseUrl { get; init; } = string.Empty;

    public string? ApiKey { get; init; }

    public string? BearerToken { get; init; }

    public TimeSpan Timeout { get; init; } = TimeSpan.FromSeconds(120);
}
