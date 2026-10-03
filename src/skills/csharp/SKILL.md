---
name: paws-csharp
description: C#/.NET specifics for paws. Use only for C#, .NET, ASP.NET Core work
---
Follow paws for style, scope, testing. Adds C# only:
- records, primary constructors, expression-bodied members, `var`, minimal APIs/top-level statements
- No interface for one implementation, XML docs on obvious members, async twin of a sync method
- Built-ins (LINQ, System.Text.Json) over helpers
- Tests: `dotnet test --filter` on changed projects
