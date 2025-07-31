#!/usr/bin/env python3

"""
Test Phase 1 execution with job architecture loading fix
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path
src_path = os.path.join(os.path.dirname(__file__), 'src')
if os.path.exists(src_path) and src_path not in sys.path:
    sys.path.insert(0, src_path)

from skill_similarity_engine.logging.config import setup_logging
from skill_similarity_engine.business_context.analytics_orchestrator import AnalyticsOrchestrator
from skill_similarity_engine.business_context.database_integrator import DatabaseIntegrator
from skill_similarity_engine.utils.processing_orchestrator import SimilarityProcessingOrchestrator, ProcessingConfig


def demonstrate_centralized_orchestrator(orchestrator):
    """Demonstrate the centralized processing orchestrator with real data."""
    print("🎯 Demonstrating Centralized Processing Orchestrator")
    print("=" * 60)
    print()
    
    try:
        # Setup enhanced similarity components
        enhanced_components = orchestrator._setup_enhanced_similarity()
        if not enhanced_components:
            print("❌ No enhanced components available for demonstration")
            return
        
        job_to_skills = enhanced_components['job_to_skills']
        job_defining_skills = enhanced_components['defining_skills_map']
        job_ids = list(job_to_skills.keys())[:50]  # Use first 50 jobs for demo
        
        print(f"📊 Using {len(job_ids)} jobs for orchestrator demonstration")
        
        # Get the rarity calculator
        rarity_calculator = orchestrator.rarity_calculator
        
        # Create job pairs for demonstration (smaller subset)
        import itertools
        job_pairs = list(itertools.combinations(job_ids, 2))[:100]  # First 100 pairs
        print(f"🔄 Processing {len(job_pairs)} job similarity pairs")
        print()
        
        # Create processing configuration
        config = ProcessingConfig(
            memory_threshold_mb=500.0,  # Lower threshold for demo
            item_size_estimate_bytes=300.0,
            target_chunk_count=5,  # Fewer chunks for demo
            min_chunk_size=20,
            max_chunk_size=50,
            progress_desc="Orchestrator Demo",
            show_memory_tracking=True
        )
        
        # Initialize the centralized orchestrator
        processing_orchestrator = SimilarityProcessingOrchestrator(config)
        
        # Show processing estimates
        estimates = processing_orchestrator.estimate_processing_requirements(len(job_pairs))
        print("📈 Processing Estimates:")
        print(f"   • Total pairs: {estimates['num_pairs']:,}")
        print(f"   • Estimated memory: {estimates['estimated_memory_mb']:.1f} MB")
        print(f"   • Strategy: {estimates['processing_strategy']}")
        print(f"   • Recommended chunk size: {estimates['recommended_chunk_size']:,}")
        print(f"   • Estimated chunks: {estimates['estimated_chunks']}")
        print()
        
        # Convert pairs to the format expected by the orchestrator
        job_pair_tuples = [(pair[0], pair[1]) for pair in job_pairs]
        
        # Process using the centralized orchestrator with CPU tracking
        print("🚀 Processing with Centralized Orchestrator + CPU Tracking...")
        
        # First, run a quick benchmark to see if parallel processing helps
        print("🏁 Running quick benchmark (parallel vs sequential)...")
        benchmark_sample = job_pair_tuples[:10]  # Small sample for quick benchmark
        benchmark_results = processing_orchestrator.benchmark_processing_strategies(
            calculator=rarity_calculator,
            job_pairs_sample=benchmark_sample,
            job_to_skills=job_to_skills,
            job_defining_skills=job_defining_skills
        )
        
        print("📊 Benchmark Results:")
        print(f"   • Sequential time: {benchmark_results['sequential_time']:.2f}s")
        print(f"   • Parallel time: {benchmark_results['parallel_time']:.2f}s") 
        print(f"   • Actual speedup: {benchmark_results['actual_speedup']:.2f}x")
        print(f"   • Parallel efficiency: {benchmark_results['parallel_efficiency_percent']:.1f}%")
        
        for rec in benchmark_results.get('recommendations', []):
            print(f"   {rec}")
        print()
        
        # Now process the full dataset
        results = processing_orchestrator.process_job_similarities(
            calculator=rarity_calculator,
            job_pairs=job_pair_tuples,
            job_to_skills=job_to_skills,
            job_defining_skills=job_defining_skills,
            use_intelligent_processing=True
        )
        
        # Show results
        successful_results = [r for r in results if r['similarity_score'] > 0]
        print(f"✅ Orchestrator completed successfully!")
        print(f"   📊 Total results: {len(results):,}")
        print(f"   📈 Successful calculations: {len(successful_results):,}")
        
        if successful_results:
            avg_similarity = sum(r['similarity_score'] for r in successful_results) / len(successful_results)
            print(f"   📊 Average similarity score: {avg_similarity:.3f}")
        
        print()
        print("🎉 Centralized Orchestrator Benefits Demonstrated:")
        print("   • Clean separation: similarity algorithms focus on core logic")
        print("   • Centralized utils: processing strategies handled in one place")
        print("   • Flexible orchestration: easy to switch between strategies")
        print("   • Maintainable architecture: changes in one place affect all entry points")
        print()
        
    except Exception as e:
        print(f"❌ Error during orchestrator demonstration: {e}")
        import traceback
        traceback.print_exc()



def main():
    """Test Phase 1 execution with enhanced processing utilities."""
    print("🧠 Testing Phase 1 Enhanced Similarity Analytics...")
    print("   This will calculate enhanced job similarities using rarity-weighted algorithms")
    print("   and populate analytics tables directly in your database.")
    print()
    print("🔧 Enhanced with centralized processing orchestrator:")
    print("   • Intelligent progress tracking (smart chunking)")
    print("   • Memory-aware adaptive processing")
    print("   • CPU utilization tracking and analysis")
    print("   • Parallel vs sequential benchmarking")
    print("   • Centralized utils coordination")
    print("   • Clean separation of algorithm vs. orchestration concerns")
    print()
    
    # Setup logging
    setup_logging(level='INFO')
    
    # Initialize orchestrator
    orchestrator = AnalyticsOrchestrator()
    
    try:
        print(f"📊 Database: {orchestrator.db_path}")
        
        # Show what we're about to do with enhanced processing
        print("\n🔍 Phase 1 Enhanced Processing will:")
        print("   • Load 715 jobs and ~2,059 skills from database")
        print("   • Calculate enhanced similarities for 510,510 job pairs")
        print("   • Use intelligent progress tracking for real-time feedback")
        print("   • Apply memory-aware processing strategies")
        print("   • Generate skill rarity analysis")
        print("   • Identify defining skills for each job")
        print("   • Populate 3 analytics tables with results")
        print()
        
        input("Press Enter to start Phase 1 execution with enhanced processing...")
        print()
        
        # First, demonstrate the centralized orchestrator
        demonstrate_centralized_orchestrator(orchestrator)
        
        # Execute Phase 1 with enhanced processing (includes corpus normalization)
        print("\n🎯 Executing Phase 1 with configuration-driven parameters:")
        print("   • Parameters loaded from: config/core/similarity_parameters.yaml")
        print("   • Defining skills threshold: 8.8% (Optuna-optimized)")
        print("   • Multiplier: 1.206x (Optuna-optimized)")
        print("   • Asymmetric Jaccard similarity (Job A → Job B career pathways)")
        print("   • Corpus-wide normalization to preserve differentiation")
        print("   • All critical values externalized from code")
        print()
        
        success = orchestrator.execute_phase_1_enhanced_similarity()
        
        if success:
            print("\n✅ Phase 1 execution successful!")
            
            # Check results
            integrator = DatabaseIntegrator(orchestrator.db_path)
            summary = integrator.get_analytics_summary()
            
            print("\n📊 Analytics Database Summary:")
            print("=" * 60)
            
            phase1_tables = [
                ('analytics_job_similarities', 'Job Similarity Pairs'),
                ('analytics_skill_rarity', 'Skill Rarity Analysis'), 
                ('analytics_job_defining_skills', 'Job Defining Skills')
            ]
            
            for table, description in phase1_tables:
                count = summary.get(table, 0)
                status = "✅" if count > 0 else "❌"
                print(f"   {status} {description:<25} {count:>10,} records")
            
            # Show total analytics records
            total_records = sum(summary.get(table, 0) for table in [t[0] for t in phase1_tables])
            print("-" * 60)
            print(f"   🎯 Total Phase 1 Records:      {total_records:>10,}")
            print("=" * 60)
            
            if total_records > 0:
                print("\n🎉 Phase 1 Enhanced Similarity Analytics completed successfully!")
                print("   Your database now contains enhanced similarity data for career intelligence.")
                print("\n📈 What you can now do:")
                print("   • Query job similarities through main.py option 3")
                print("   • Use the analytics tables for custom analysis")
                print("   • Run Phase 2 and 3 for additional insights")
                print("\n🚀 Processing Enhancements Used:")
                print("   • Smart progress tracking automatically selected optimal strategy")
                print("   • Memory-aware processing prevented out-of-memory issues")
                print("   • CPU utilization tracking provided performance insights")
                print("   • Centralized orchestrator managed all processing strategies")
                print("   • Modular architecture enabled clean separation of concerns")
            else:
                print("\n⚠️ Phase 1 completed but no records were generated.")
                print("   This indicates the SkillIntelligenceEngine didn't load data properly.")
                print("   Check the logs above for 'Enhanced similarity components loaded' message.")
                
        else:
            print("\n❌ Phase 1 execution failed")
            print("   Check the logs above for error details.")
            
    except Exception as e:
        print(f"💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()