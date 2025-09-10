#!/usr/bin/env python3
"""
Script para executar classificação em lotes maiores
"""

from session_classifier import SessionClassifier
import time

def run_classification_batches(total_sessions: int = 100, batch_size: int = 10):
    """Executa classificação em lotes com intervalo entre chamadas"""
    
    classifier = SessionClassifier()
    processed = 0
    
    print(f"🎯 Meta: classificar {total_sessions} sessões em lotes de {batch_size}")
    
    while processed < total_sessions:
        print(f"\n{'='*60}")
        print(f"🔄 Lote {processed//batch_size + 1} - Processando sessões {processed+1}-{min(processed+batch_size, total_sessions)}")
        
        # Verificar se ainda há sessões para classificar
        stats = classifier.get_classification_stats()
        remaining = stats['total_sessions'] - stats['total_classified']
        
        if remaining == 0:
            print("✅ Todas as sessões já foram classificadas!")
            break
        
        current_batch = min(batch_size, total_sessions - processed, remaining)
        classifier.classify_sessions(current_batch)
        
        processed += current_batch
        
        # Estatísticas atualizadas
        stats = classifier.get_classification_stats()
        print(f"\n📊 Progresso total: {stats['total_classified']}/{stats['total_sessions']} "
              f"({stats['progress_percent']:.1f}%)")
        
        if stats['categories']:
            print("\n📈 Distribuição atual:")
            for category, count in sorted(stats['categories'].items(), key=lambda x: x[1], reverse=True):
                print(f"  {category}: {count}")
        
        # Pausa entre lotes para não sobrecarregar a API
        if processed < total_sessions and remaining > 0:
            print("\n⏸️  Pausando 5 segundos...")
            time.sleep(5)
    
    # Exportar resultados finais
    classifier.export_classifications_to_csv(f"classifications_batch_{int(time.time())}.csv")
    classifier.close()
    
    print(f"\n🎉 Classificação concluída! {processed} sessões processadas.")

if __name__ == "__main__":
    # Executar classificação de 50 sessões em lotes de 5
    run_classification_batches(total_sessions=50, batch_size=5)