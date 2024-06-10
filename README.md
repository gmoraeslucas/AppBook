# AppBook


> Automação desenvolvida em Python para coleta de dados dentro do horário comercial (Dias úteis: 7:00am - 7:00pm) referentes ao ano, mês e dias do mês selecionados, de cada sistema. Os dados são gerados a partir da API DataDog e são armazenados em um arquivo JSON.

### Ajustes e melhorias

O projeto ainda está em desenvolvimento e as próximas atualizações serão voltadas nas seguintes tarefas:

- [ ] Adicionar a coleta de sistemas e serviços pendentes.

## 💻 Pré-requisitos

Antes de começar, verifique se você atendeu aos seguintes requisitos:

- Você possui a versão mais recente do `<Python>` instalada.
- Você instalou corretamente os `<requirements.txt>`;
- Você tem uma `<API_KEY>` e uma `<APPLICATION_KEY>` da DataDog, criou um arquivo `<.env>` e adicionou no diretório AppBook com as seguintes informações:
  
*.env*
```
API_KEY=xxx
APPLICATION_KEY=xxx
```

## ☕ Usando AppBook

Quando você usar a aplicação, terá que informar dois dados para a consulta:

```
Informe o Ano da consulta (YYYY):
Informe o Mês da consulta (1-12): 
```

Após finalizada a consulta, será criado no próprio diretório uma pasta que contém o arquivo JSON com os dados.
