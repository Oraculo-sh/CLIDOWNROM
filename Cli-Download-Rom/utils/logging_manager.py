# Dentro de logging_manager.py, substitua apenas a função handle_exception

def handle_exception(exc_type, exc_value, exc_traceback):
    """Captura exceções não tratadas e as registra no crash.log."""
    # Ignora o Ctrl+C para permitir que o usuário interrompa o programa
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    # Loga a exceção crítica para todos os handlers configurados (console, latest, error)
    logging.critical("Unhandled exception caught!", exc_info=(exc_type, exc_value, exc_traceback))
    
    # Adicionalmente, escreve o traceback detalhado APENAS no crash.log
    crash_log_file = log_dir / 'crash.log'
    with open(crash_log_file, 'a', encoding='utf-8') as f:
        f.write(f"\n--- CRASH REPORT - {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
        import traceback
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)