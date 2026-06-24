# Altered Agentic Patterns Lab

Starter repository in Python che trasforma i principali *agentic design pattern* in componenti piccoli, testabili e indipendenti dal fornitore del modello.

## Obiettivo

La repository non prova a costruire subito un “super-agente”. Fornisce invece una base verificabile per:

- concatenamento di passaggi;
- routing verso specialisti;
- esecuzione parallela;
- riflessione e maker-checker;
- pianificazione con criteri di completamento;
- memoria persistente minimale;
- retry e recupero dagli errori;
- guardrail deterministici;
- valutazione riproducibile.

Il codice funziona anche senza API LLM: ogni agente è una funzione Python. In produzione, tali funzioni possono essere sostituite da adapter per OpenAI, Gemini, Claude, modelli locali o server MCP.

## Avvio rapido

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\\Scripts\\activate
pip install -e .[dev]
pytest
python examples/crypto_research.py
```

## Architettura

```text
src/agentic_patterns_lab/
├── contracts.py      # contratti dati e risultati
├── patterns.py       # chain, router, parallel, reflection, planning
├── memory.py         # memoria JSON atomica
├── guardrails.py     # policy e limiti deterministici
├── recovery.py       # retry con backoff
└── evaluation.py     # metriche e tracciamento
```

## Principio di sicurezza

La proposta, la verifica e l'esecuzione sono separate. L'esempio genera una tesi di ricerca e la verifica, ma non invia ordini. Qualunque collegamento a un broker deve aggiungere approvazione umana, limiti di posizione, audit log e kill switch.

## Evoluzione consigliata

1. Aggiungere adapter per provider LLM sotto `src/agentic_patterns_lab/providers/`.
2. Aggiungere tool reali con permessi minimi sotto `tools/`.
3. Versionare prompt, dataset golden e risultati di valutazione.
4. Integrare OpenTelemetry o un sistema di tracing.
5. Implementare un server MCP solo per capacità strettamente necessarie.

## Licenza

MIT. Vedere `LICENSE`.
