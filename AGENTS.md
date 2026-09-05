# AGENTS.md

## Fluxo obrigatório

1. Crie uma Issue para toda correção, melhoria, documentação ou nova funcionalidade.
2. Crie uma branch específica a partir de main.
3. Nunca faça mudanças diretamente em main.
4. Abra um Pull Request e mencione a Issue com Closes #numero ou Refs #numero.
5. Antes do merge, execute ruff check . e pytest.
6. Atualize o README quando instalação, comportamento ou arquitetura mudarem.

## Qualidade e segurança

- Preserve credenciais exclusivamente em variáveis de ambiente.
- Mantenha cobertura mínima de 80% e testes dos comportamentos alterados.
- Use consultas SQL parametrizadas.
- Prefira alterações pequenas, legíveis e fáceis de revisar.
- Em produção, use logs estruturados e uma solução apropriada de observabilidade, como Sentry ou OpenTelemetry.

## Interfaces

Este projeto é uma API sem interface gráfica. Caso uma interface seja adicionada, aplique skeletons, lazy loading, estados de progresso, animações suaves e suporte a prefers-reduced-motion. Use Playwright para os fluxos end-to-end da interface.
