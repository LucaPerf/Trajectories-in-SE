from hackingBuddyGPT.utils.llm_util import cmd_output_fixer

r = "exec_command cat > /tmp/f.py << 'EOF'\nprint(1)\nEOF\npython3 /tmp/f.py"
print("----- risultato -----")
print(cmd_output_fixer(r))
print("----- righe:", len(cmd_output_fixer(r).splitlines()))