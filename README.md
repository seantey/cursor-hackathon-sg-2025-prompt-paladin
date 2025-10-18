# 🏰 Prompt Paladin MCP

An MCP server that assesses prompt quality in real time. It detects unclear, ambiguous, or under-specified prompts before they reach the coding agent, helping developers refine their intent and maintain clarity in every interaction.

---

## 📜 Lore

*The Citadel of Context, home of the Prompt Paladins, the last bastion against developer toxicity and sins.*  
*Within its radiant halls, they guard the fragile harmony between human and machine, cleansing corrupted code and calming the storms of misguided prompts.*  
*For in the AI realms, a single toxic word can twist intention and fracture clarity.*  

*Thus the Paladins labor endlessly, healing wounded syntax, sanctifying context, and defending the sacred art of clear and purposeful instruction.*

---

## ⚙️ Core Tools

| Tool | Description |
|------|-------------|
| **`pp-guard`** | Judges the quality of a prompt, deciding whether it proceeds or must be healed. |
| **`pp-suggestions`** | Offers refined variants of the user’s prompt for improved clarity or tone. |
| **`pp-heal`** | Rewrites unclear or corrupted prompts into clean, purposeful language. |
| **`pp-discuss`** | Engages the user in clarifying dialogue when intention is uncertain. |
| **`pp-proceed`** | Allows the user to bypass the Paladin’s intervention and continue. |

---

## ✨ Aspects of the Paladins

Within the Citadel, the Paladins embody different callings — each a facet of their sacred duty to preserve harmony between human and machine.

---

### 🩹 Healers of Clarity

*Where confusion reigns, the Healers mend it.*  
*They mend broken meaning, steady trembling context, and restore purpose to wayward prompts.*

**Toggle:** **Enable Auto-cast Heal**  
**Function:** Automatically detects and heals unclear or malformed prompts before they reach the coding agent.  

**System message:**  
🩹 *Auto-cast Heal activated — your prompt was healed for clarity.*

---

### 🕊️ Translators of Wrath

*Among the Paladins there are also the Translators of Wrath — gentle souls who listen to fury and return peace.*  
*They do not punish anger; they simply render it harmless.*

**Toggle:** **Enable Anger Translator**  
**Function:** Transforms frustration, sarcasm, or profanity into calm and constructive intent — keeping communication clear even in moments of irritation.  

**System message:**  
🕊️ *Anger Translator active — your frustration has been rephrased into reason.*

---

## ⚙️ Configuration Example

```json
{
  "prompt_paladin": {
    "auto_cast_heal": true,
    "anger_translator": true
  }
}
````

---

### 🧭 Flow

```
User Prompt
  ↓
pp-guard
  ↓
If unclear → Healers of Clarity (Auto-cast Heal)
If angry → Translators of Wrath (Anger Translator)
Else → proceed
```

---

### 🧩 Interaction in Cursor

*(Placeholder for screenshot: three-button UI in Cursor)*
**[Screenshot coming soon — showing the Prompt Paladin intervention panel with buttons]**

When `pp-guard` intervenes, the user is shown three choices:

| Button                 | Description                                                                  |
| ---------------------- | ---------------------------------------------------------------------------- |
| **💡 Suggest Fix**     | Opens `pp-suggestions`, offering 2–3 refined versions of your prompt.        |
| **✨ Heal Prompt**      | Invokes `pp-heal` to automatically rewrite your prompt for clarity and tone. |
| **🚀 Proceed Anyways** | Calls `pp-proceed`, allowing the user to bypass the Paladin and continue.    |

If the user types free text instead of clicking a button, the system calls **`pp-discuss`**, opening a short dialogue to clarify intent.

*Each choice reflects a different Paladin virtue — counsel, healing, or trust.*

---

### 🛡️ The Paladin’s Oath

*“To heal is mercy. To translate wrath is grace. To guard is duty.”*

---

### 🧾 License

This project is licensed under the [MIT License](LICENSE).
