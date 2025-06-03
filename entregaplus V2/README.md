## 📕 Introdução

### 🔐 Sistema de Autenticação Inteligente com IA – Delivery

 Este projeto tem como objetivo implementar um sistema de autenticação moderno e seguro, utilizando Inteligência Artificial (IA) para analisar e gerar logs de login detalhados. A IA é aplicada para identificar padrões suspeitos de acesso, ajudando a detectar possíveis fraudes ou invasões em tempo real.

---

### 🤖 Como a IA é utilizada?

 A IA é treinada com dados históricos de login para aprender o comportamento normal dos usuários. Com isso, ela consegue identificar tentativas suspeitas, como por exemplo:

 - Múltiplas tentativas de login em um curto intervalo de tempo;

 - Acesso feito por IPs distintos e desconhecidos;

 - Acessos realizados em horários incomuns ou de localizações inesperadas;

 - Usuário digitando senha incorreta três vezes seguidas (isso bloqueia a conta por 30 segundos e marca como suspeito).

 - Essas situações são analisadas automaticamente e, quando detectadas, são registradas e classificadas para que um administrador possa tomar as devidas ações.

---

### 📋 O que é registrado no sistema de logs?

 O sistema salva informações importantes a cada tentativa de login:

 - Usuário: o e-mail do usuário que tentou acessar;

 - IP de origem: usado para verificar localização e padrões de uso;

 - Horário do acesso: data e hora da tentativa;

 - Sucesso ou falha: se a tentativa foi bem-sucedida ou não;

 - Motivo: exemplo: "Senha incorreta" ou "Usuário não encontrado";

 - Número de falhas consecutivas;

 - Quantidade de IPs distintos usados na conta;

 - Classificação do login: “Normal” ou “Suspeito” (definido pela IA);

 - Campo suspeito (True/False): indica se o login foi identificado como potencial ameaça.

 Esses dados são armazenados:

 - Em um banco de dados com SQLAlchemy;

 - Em um arquivo .txt para fins de auditoria;

---

### 🧔‍♂️ Painel do Administrador 

 Apenas usuários administradores podem acessar o painel onde:

 - Todos os logs são listados em forma de tabela;

 - Tentativas suspeitas são destacadas visualmente;

 - Ações futuras de segurança podem ser tomadas com base nos alertas.

### 🖥️ Tecnologias utilizadas: 
```bash
 Python 3.12
 Flask
 Flask-Login
 SQLAlchemy
 scikit-learn (IA / machine learning)
 Pandas
 HTML
 CSV
 ```