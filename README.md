# 🤖 Bot Educacional de Inglês para Discord

Um bot avançado para Discord projetado para ensinar inglês através de interações conversacionais, processamento de voz e conteúdo personalizado.

## 🌟 Funcionalidades

- Sistema conversacional para ensino de inglês com múltiplos níveis
- Processamento de mensagens de voz para avaliação de pronúncia
- Geração de conteúdo educativo personalizado
- Sistema de acompanhamento de progresso do aluno
- Exercícios, correções e explicações gramaticais

## 🔧 Configuração

1. Clone este repositório
2. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```
3. Copie o arquivo `.env.example` para `.env` e configure as variáveis:
   ```
   cp .env.example .env
   ```
4. Adicione seu token do Discord e chave API da OpenAI no arquivo `.env`

## 🚀 Executando o Bot

Para iniciar o bot, execute:

```
python src/main.py
```

## 📋 Comandos Disponíveis

- `!help` - Exibe a lista de comandos disponíveis
- `!learn [tópico]` - Inicia uma sessão de aprendizado sobre um tópico
- `!practice` - Inicia uma sessão de prática conversacional
- `!progress` - Exibe o progresso do usuário
- `!pronounce [texto]` - Avalia a pronúncia de uma frase em inglês

## 🏗️ Arquitetura

Este projeto segue os princípios de Clean Architecture e SOLID, dividido em:

- **Domain**: Entidades e regras de negócio
- **Application**: Casos de uso e serviços
- **Infrastructure**: Implementações concretas (APIs externas, banco de dados)
- **Presentation**: Interface com o Discord e comandos

## 📝 Licença

MIT
