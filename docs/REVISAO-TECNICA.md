# Revisão técnica — Customer Management API

Revisão de 10/10/2026, vinculada à Issue #3. Foco: avaliar a implementação como evidência de prática para Back-End Júnior.

## Pontos fortes

- CRUD completo com criação 201, tratamento de cliente inexistente 404 e validação 422.
- SQL parametrizado nas operações que recebem entradas.
- Credenciais lidas de variáveis de ambiente, com suporte a `.env` local.
- Documentação interativa pelo FastAPI.
- Testes HTTP com banco simulado e pipeline de qualidade exigindo cobertura mínima de 80%.

## Achados na versão revisada e ordem sugerida

1. **Validação de entrada:** o nome usa apenas limites de tamanho. Dois espaços atendem ao mínimo de dois caracteres. O e-mail verifica a presença de `@` e de ponto no domínio, sem validar a parte local ou proibir espaços internos. Reforçar essas regras e adicionar testes específicos antes de anunciar validação completa.
2. **Falhas do banco:** conexão e criação do cursor ocorrem antes do `try/finally`. Se o cursor falhar, o fechamento da conexão não é executado por esse bloco. Cobrir a aquisição e liberação dos recursos e definir respostas controladas para indisponibilidade, sem expor credenciais ou detalhes SQL ao cliente.
3. **Integração real:** os testes atuais usam objetos simulados. Adicionar testes com MySQL isolado para comprovar esquema, persistência, commit e comportamento em falhas. Não usar o banco comercial de outro projeto.
4. **Evolução do contrato:** adicionar paginação da listagem e definir política de duplicidade de e-mail conforme o problema de negócio. Hoje o esquema do README não exige e-mails únicos.
5. **Uso público com dados reais:** definir autenticação, autorização e observabilidade antes de disponibilizar operações sobre cadastros reais.

Não é necessário trocar a linguagem ou criar uma arquitetura extensa para resolver esses pontos. Mudanças pequenas, acompanhadas de testes dos comportamentos alterados, permitem explicar melhor as decisões.

### Validação corrigida no PR #6

O primeiro achado foi tratado: nomes têm espaços das extremidades removidos antes dos limites de tamanho e e-mails são validados com `EmailStr`, mantendo a normalização para minúsculas. Os testes cobrem POST e PUT e verificam que entradas inválidas retornam 422 sem abrir conexão com o banco. O formato válido não comprova a existência ou a propriedade do endereço.

O pipeline da correção aprovou 34 testes e cobertura de 98,73%.

### Falhas do MySQL tratadas na Issue #7

O segundo achado recebeu aquisição e liberação centralizadas dos recursos, HTTP 503 para erros operacionais/de comunicação e HTTP 500 genérico para outros erros MySQL. Falhas de escrita incluem tentativa de rollback; falhas MySQL de limpeza não ocultam a resposta original e não impedem a tentativa de fechar a conexão.

Não há repetição automática de escritas. Testes simulam falhas de conexão, cursor, execução, leitura, commit, rollback e fechamento. A integração com MySQL real, paginação e controle de acesso continuam como próximos passos.

## Verificação

O pipeline de main consultado nesta revisão aprovou 10 testes, com cobertura de 98,78% do módulo `app`. Execução: https://github.com/morettichaves/customer-management-api/actions/runs/33963733798.

Essa cobertura mede as linhas exercitadas; a função de conexão real está substituída nos testes. Não foram acessados bancos comerciais nem feitas mudanças no JSilva ou no portfólio publicado.

## Escopo da entrega

Este PR documenta o estado atual, inclui `.env.example` e torna a instalação e os limites mais claros. Não altera rotas, validações ou banco. As correções sugeridas devem ser implementadas em trabalhos próprios, com Issue, branch, testes e PR conforme `AGENTS.md`.
