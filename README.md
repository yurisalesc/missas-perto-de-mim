![status](https://img.shields.io/badge/status-ativo-0f766e) ![stack](https://img.shields.io/badge/stack-FastAPI%20%7C%20PostgreSQL%20%7C%20Vite-2563eb) ![contribuições](https://img.shields.io/badge/contribui%C3%A7%C3%B5es-bem--vindas-16a34a)

# Missas Perto de Mim 🙏:church:

Encontre missas com mais facilidade, por cidade e por proximidade, em uma experiência simples e direta.



## ✨ Visão rápida

| Funcionalidade | O que você encontra |
|---|---|
| 🔎 **Busca inteligente** | Missas por cidade, raio e janela de horário |
| 🗺️ **Mapa interativo** | Igrejas plotadas com ação de foco no mapa |
| ⏰ **Acontecendo agora** | Missas em andamento no momento da busca |
| ℹ️ **Info da igreja** | Telefone, redes sociais/site e observações |

## 💡 O que o sistema faz

- Buscar missas na aba **Home** usando cidade, raio e horário.
- Listar **todas as missas** por cidade e/ou nome da igreja.
- Mostrar **missas acontecendo agora**.
- Exibir resultados no mapa com ações rápidas por igreja.

Este README foca no uso público da plataforma e na contribuição de dados da comunidade.

## Tecnologias

- API: FastAPI + SQLAlchemy
- Banco: PostgreSQL
- Frontend: HTML, CSS e JavaScript (Vite)
- Mapa: Leaflet + OpenStreetMap

## Como rodar localmente

### 1) Subir API e banco

```bash
docker compose up -d --build
```

API disponível em:
- `http://127.0.0.1:8000`

### 2) Subir frontend

```bash
cd apps/web
npx --yes vite --host 127.0.0.1 --port 5173
```

App disponível em:
- `http://127.0.0.1:5173`

## Como contribuir com dados (planilha CSV)

Você pode contribuir enviando uma planilha com igrejas, contatos e horários. 🤝

### Estrutura da planilha (formato CSV)

| Nome da Instituição | Categoria | Endereço | Telefone | Redes Sociais/Site | Cidade | Estado | Seg | Ter | Qua | Qui | Sex | Sab | Dom | Flags |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Catedral Metropolitana de N. Sra. da Apresentação | Catedral | Av. Floriano Peixoto, 674, Tirol | (84) 3201-4559 | @paroquiadacatedraldenatal | Natal | RN | 11:00, 16:30 | 11:00, 16:30 | 11:00, 16:30 | 11:00, 16:30 | 11:00, 16:30 | 11:00, 16:30 | 07:00, 11:00, 19:00 | Sede Arquidiocesana |
| Igreja Matriz de N. Sra. da Apresentação (Antiga) | Co-Catedral | Praça André de Albuquerque, s/n, Cidade Alta | (84) 3615-2808 | arquidiocesedenatal.org.br | Natal | RN |  | 16:30 | 16:30 | 16:30 | 16:30 | 16:30 | 07:00, 16:30 | Centro Histórico |

### Exemplo em CSV (copiar e colar)

```csv
Nome da Instituição,Categoria,Endereço,Telefone,Redes Sociais/Site,Cidade,Estado,Seg,Ter,Qua,Qui,Sex,Sab,Dom,Flags
Catedral Metropolitana de N. Sra. da Apresentação,Catedral,"Av. Floriano Peixoto, 674, Tirol",(84) 3201-4559,@paroquiadacatedraldenatal,Natal,RN,"11:00, 16:30","11:00, 16:30","11:00, 16:30","11:00, 16:30","11:00, 16:30","11:00, 16:30","07:00, 11:00, 19:00",Sede Arquidiocesana
Igreja Matriz de N. Sra. da Apresentação (Antiga),Co-Catedral,"Praça André de Albuquerque, s/n, Cidade Alta",(84) 3615-2808,arquidiocesedenatal.org.br,Natal,RN,,16:30,16:30,16:30,16:30,16:30,"07:00, 16:30",Centro Histórico
```

### Regras de preenchimento

- Horários no formato `HH:MM`.
- Se houver mais de um horário no mesmo dia, separar por vírgula (ex.: `"07:00, 11:00, 19:00"`).
- Se não houver missa no dia, deixar a célula vazia.
- Em `Flags`, inclua observações úteis (ex.: missa especial, adoração, comunidade específica).

### Envio da contribuição

- Abra uma issue com o CSV anexado ou envie por e-mail para yuri.sales@protonmail.com

Obrigado por contribuir com a comunidade. 💚

