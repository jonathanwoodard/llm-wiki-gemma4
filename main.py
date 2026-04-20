import os
import re
import json
import typer
import ollama
from typing import Dict, Any
import tools 

app = typer.Typer()

class AgentRunner:
    def __init__(self, model_name: str, max_cycles: int = 35):
        self.model_name = model_name
        self.max_cycles = max_cycles
        self.current_cycle = 0
        self.last_tool = None
        self.consecutive_count = 0
        self.context_files = ["AGENT_SCHEMA.md", "llm-wiki.md"]
        self.system_prompt_template = self._assemble_prompt_template()
        
        # Ensure the base wiki directory exists before checking contents
        os.makedirs("wiki", exist_ok=True)
        self._ensure_wiki_structure()

        self.tool_registry: Dict[str, Any] = {
            "read_document": tools.read_document,
            "write_file": tools.write_file,
            "append_to_file": tools.append_to_file,
            "search_wiki": tools.search_wiki,
            "get_file_metadata": tools.get_file_metadata,
            "list_directory": tools.list_directory,
            "web_scrape": tools.web_scrape,
            "check_broken_links": tools.check_broken_links,
            "find_orphan_pages": tools.find_orphan_pages,
            "rebuild_index": tools.rebuild_wiki_index,
        }

    def _ensure_wiki_structure(self):
        """Checks for core wiki files, prompting user to create them if missing."""
        core_files = [
            "wiki/index.md",
            "wiki/log.md",
            "wiki/overview.md",
            "wiki/glossary.md",
            "wiki/bibliography.md"
        ]

        missing_files = [f for f in core_files if not os.path.exists(f)]

        if not missing_files:
            return

        typer.secho("\n⚠️  Wiki Structure Warning: Missing core files.", fg=typer.colors.YELLOW)
        
        if typer.confirm("Would you like me to initialize the missing wiki components?"):
            # Create files
            for f in missing_files:
                # Ensure parent dir exists (in case a file path was inside a missing dir)
                os.makedirs(os.path.dirname(f), exist_ok=True)
                with open(f, 'w', encoding='utf-8') as file:
                    file.write("") # Create empty file
                typer.echo(f"Created file: {f}")
            
            typer.secho("✅ Wiki structure initialized successfully.", fg=typer.colors.GREEN)
        else:
            typer.secho("❌ User declined initialization. Running in partial mode.", fg=typer.colors.RED)

    def _assemble_prompt_template(self) -> str:
        combined_context = ["You are a Wiki Librarian. Follow the LLM-Wiki pattern: Thought/Action/Input/Observation/Response."]
        for file_path in self.context_files:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    combined_context.append(f.read())
        return "\n\n".join(combined_context)

    def _get_current_turn_system_prompt(self) -> str:
        progress_info = f"\n\n[SYSTEM NOTICE: You have performed {self.current_cycle} actions this turn. You have {self.max_cycles - self.current_cycle} actions remaining before you must stop and check in with the user.]"
        return self.system_prompt_template + progress_info

    def parse_llm_output(self, text: str) -> Dict[str, str]:
        patterns = {
            "thought": r"Thought:\s*(.*?)(?=\nAction:|\nResponse:|$)",
            "action": r"Action:\s*(.*?)(?=\nInput:|\nResponse:|$)",
            "input": r"Input:\s*(\{.*?\})",
            "response": r"Response:\s*(.*)"
        }
        extracted = {}
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.DOTALL)
            extracted[key] = match.group(1).strip() if match else None
        return extracted

    def execute_tool(self, action_name: str, tool_input: str) -> str:
        if action_name not in self.tool_registry:
            return f"Error: Tool '{action_name}' is not registered."
        observation = ""
        try:
            params = json.loads(tool_input)
            observation = self.tool_registry[action_name](**params)
            
            # PROPOSED CHANGE: Auto-rebuild index after any wiki write
            if action_name in ["write_file", "append_to_file"]:
                if "wiki/" in params.get("path", ""):
                    tools.rebuild_wiki_index("wiki/index.md", "wiki")
                    observation += " (System Note: wiki/index.md was automatically rebuilt)"
            
            return observation
        except Exception as e:
            return f"Error: {str(e)}"

    def run_session(self):
        typer.echo(f"🚀 LLM-Wiki Engine Started [{self.model_name}]")
        messages = [{"role": "system", "content": self._get_current_turn_system_prompt()}]

        # NEW: Automated Session Start
        initial_prompt = "Execute the Session Start Checklist as defined in llm-wiki.md."
        messages.append({"role": "user", "content": initial_prompt})

        # Process the checklist automatically before entering the user loop
        self._run_agent_loop(messages)

        try:
            while True:
                user_input = typer.prompt("User")
                if user_input.lower() in ["exit", "quit", "stop"]: 
                    break
                
                messages.append({"role": "user", "content": user_input})
                self._run_agent_loop(messages)
        except KeyboardInterrupt:
            typer.secho("\n🛑 Session Ended.", fg=typer.colors.RED)

    def _run_agent_loop(self, messages):
        """Refactored logic to allow the agent to chain multiple actions autonomously."""
        self.current_cycle = 0
        for _ in range(self.max_cycles):
            messages[0] = {"role": "system", "content": self._get_current_turn_system_prompt()}
            response = ollama.chat(model=self.model_name, messages=messages)
            assistant_text = response['message']['content']
            messages.append({"role": "assistant", "content": assistant_text})
            
            parsed = self.parse_llm_output(assistant_text)

            # If the agent is done and providing a final response to the user
            if parsed.get("response"):
                typer.secho(f"\n[Agent]: {parsed['response']}", fg=typer.colors.GREEN)
                return 

            # If the agent is performing an action
            if parsed.get("action") and parsed.get("input"):
                action = parsed["action"]
                observation = self.execute_tool(action, parsed["input"])
                self.current_cycle += 1
                typer.echo(f"🛠️  Action: {action} | 👁️  Observation: {observation[:100]}...")
                messages.append({"role": "user", "content": f"Observation: {observation}"})
            
            if self.current_cycle >= self.max_cycles:
                typer.secho("\n⚠️ Action limit reached. Stopping for safety.", fg=typer.colors.RED)
                break

if __name__ == "__main__":
    # Ensure a basic wiki structure exists
    os.makedirs("wiki", exist_ok=True)
    os.makedirs("raw", exist_ok=True)
    
    runner = AgentRunner(model_name="gemma4-stable") # Or your preferred local model
    runner.run_session()
