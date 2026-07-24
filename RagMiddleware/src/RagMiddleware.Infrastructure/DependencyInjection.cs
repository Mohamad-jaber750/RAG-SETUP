using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Options;
using Polly;
using Polly.Extensions.Http;
using RagMiddleware.Application.Auditing;
using RagMiddleware.Application.Options;
using RagMiddleware.Application.Rag;
using RagMiddleware.Application.Users;
using RagMiddleware.Infrastructure.Auditing;
using RagMiddleware.Infrastructure.Persistence;
using RagMiddleware.Infrastructure.Rag;
using RagMiddleware.Infrastructure.Users;

namespace RagMiddleware.Infrastructure;

public static class DependencyInjection
{
    public static IServiceCollection AddInfrastructure(this IServiceCollection services, IConfiguration configuration)
    {
        services.AddSingleton<MongoDbContext>();
        services.AddScoped<IUserRepository, MongoUserRepository>();
        services.AddScoped<IAuditLogService, AuditLogService>();

        services.AddHttpClient<IRagApiClient, RagApiClient>((provider, client) =>
        {
            var options = provider.GetRequiredService<IOptions<RagApiOptions>>().Value;
            client.BaseAddress = new Uri(options.BaseUrl);
            client.Timeout = options.Timeout;
        }).AddPolicyHandler(request =>
            request.Method == HttpMethod.Get
                ? HttpPolicyExtensions
                    .HandleTransientHttpError()
                    .WaitAndRetryAsync(3, attempt => TimeSpan.FromMilliseconds(200 * Math.Pow(2, attempt)))
                : Policy.NoOpAsync<HttpResponseMessage>());

        return services;
    }
}
