"""
Main Pipeline class - orchestrates all stages.
"""
from datetime import datetime
from typing import Optional, List, Type

from loguru import logger

from src.pipeline.context import PipelineContext
from src.pipeline.base import Stage, PipelineComponent
from src.pipeline.stages import (
    ParsingStage,
    AggregationStage,
    SummarizationStage,
    TextProcessingStage,
    VoicePreparationStage,
    SynthesisStage,
    VoiceConversionStage,
    PublishingStage,
)


class Pipeline:
    """
    Главный класс Pipeline.
    
    Orchestrates all stages and manages the pipeline lifecycle.
    
    Usage:
        pipeline = PipelineBuilder()\
            .with_parsing(parser)\
            .with_aggregation()\
            .with_summarization(summarizer)\
            .with_tts(tts_engine)\
            .with_publishing(publisher)\
            .build()
        
        success = pipeline.run()
    """
    
    def __init__(self, stages: Optional[List[Stage]] = None):
        self._stages = stages or []
        self._logger = logger.bind(pipeline=True)
    
    @property
    def stages(self) -> List[Stage]:
        """List of stages in the pipeline."""
        return self._stages
    
    def add_stage(self, stage: Stage) -> "Pipeline":
        """Add a stage to the pipeline. Returns self for chaining."""
        self._stages.append(stage)
        return self
    
    def setup(self) -> None:
        """Setup all stages and components before running."""
        self._logger.info(f"Setting up pipeline with {len(self._stages)} stages...")
        
        for stage in self._stages:
            if stage.enabled:
                self._logger.debug(f"Setting up stage: {stage.name}")
                try:
                    stage.setup()
                except Exception as e:
                    self._logger.warning(f"Stage '{stage.name}' setup failed: {e}")
    
    def teardown(self) -> None:
        """Teardown all stages and components after running."""
        self._logger.info("Tearing down pipeline...")
        
        for stage in self._stages:
            if stage.enabled:
                try:
                    stage.teardown()
                except Exception as e:
                    self._logger.warning(f"Stage '{stage.name}' teardown failed: {e}")
    
    def run(self) -> bool:
        """
        Run the complete pipeline.
        
        Returns:
            True if pipeline completed successfully, False otherwise.
        """
        self._logger.info("=" * 60)
        self._logger.info("Pipeline started")
        self._logger.info("=" * 60)
        
        # Create context
        context = PipelineContext()
        context.start_time = datetime.now()
        
        # Setup
        self.setup()
        
        try:
            # Run stages sequentially
            for stage in self._stages:
                if not stage.enabled:
                    self._logger.debug(f"Skipping disabled stage: {stage.name}")
                    continue
                
                self._logger.info(f"\n{'─' * 40}")
                self._logger.info(f"Starting stage: {stage.name}")
                self._logger.info(f"{'─' * 40}")
                
                context = stage.execute(context)
                
                # Check for errors
                if context.has_errors:
                    self._logger.error(
                        f"Stage '{stage.name}' produced errors, stopping pipeline"
                    )
                    break
                
                # Log stage summary
                self._logger.info(
                    f"Stage '{stage.name}' completed. "
                    f"Context: {context}"
                )
            
            # Final status
            success = context.success
            
            if success:
                self._logger.info("=" * 60)
                self._logger.info("Pipeline completed successfully!")
                self._logger.info("=" * 60)
            else:
                self._logger.error("=" * 60)
                self._logger.error("Pipeline finished with errors")
                self._logger.error(f"Errors: {context.errors}")
                self._logger.error("=" * 60)
            
            return success
            
        except Exception as e:
            self._logger.exception(f"Pipeline failed with exception: {e}")
            context.add_error(str(e))
            return False
            
        finally:
            # Always teardown
            self.teardown()
            
            # Log final summary
            if context.start_time:
                duration = (datetime.now() - context.start_time).total_seconds()
                self._logger.info(f"Total duration: {duration:.1f} seconds")


# =============================================================================
# Pipeline Builder
# =============================================================================

class PipelineBuilder:
    """
    Builder for creating Pipeline instances with fluent interface.
    
    Usage:
        pipeline = (PipelineBuilder()
            .with_parsing(parser)
            .with_aggregation()
            .with_summarization(summarizer, prefix="...", suffix="...")
            .with_text_processing(accentor=True, yo_replacer=False)
            .with_tts(tts_engine, use_voice_clone=True)
            .with_publishing(publisher)
            .build())
    """
    
    def __init__(self):
        self._stages: List[Stage] = []
        
        # Stage configurations
        self._parsing_enabled = True
        self._aggregation_enabled = True
        self._summarization_enabled = True
        self._text_processing_enabled = False
        self._voice_preparation_enabled = False
        self._synthesis_enabled = True
        self._voice_conversion_enabled = False
        self._publishing_enabled = True
    
    # -------------------------------------------------------------------------
    # Stage configurations
    # -------------------------------------------------------------------------
    
    def with_parsing(self, parser, enabled: bool = True) -> "PipelineBuilder":
        """Configure parsing stage."""
        from src.pipeline.components import ParserComponent
        
        self._parsing_enabled = enabled
        stage = ParsingStage(enabled=enabled)
        stage.add_component(ParserComponent(parser=parser, enabled=enabled))
        self._stages.append(stage)
        return self
    
    def with_aggregation(
        self,
        aggregator_type: str = "default",
        enabled: bool = True
    ) -> "PipelineBuilder":
        """Configure aggregation stage."""
        from src.pipeline.components import DefaultAggregator, StructuredAggregator
        
        self._aggregation_enabled = enabled
        stage = AggregationStage(enabled=enabled)
        
        if aggregator_type == "structured":
            stage.add_component(StructuredAggregator(enabled=enabled))
        else:
            stage.add_component(DefaultAggregator(enabled=enabled))
        
        self._stages.append(stage)
        return self
    
    def with_summarization(
        self,
        summarizer,
        prefix: str = "",
        suffix: str = "",
        enabled: bool = True
    ) -> "PipelineBuilder":
        """Configure summarization stage."""
        from src.pipeline.components import LLMSummarizerComponent
        
        self._summarization_enabled = enabled
        stage = SummarizationStage(enabled=enabled)
        
        stage.add_component(
            LLMSummarizerComponent(
                summarizer=summarizer,
                prefix=prefix,
                suffix=suffix,
                enabled=enabled
            )
        )
        
        self._stages.append(stage)
        return self
    
    def with_text_processing(
        self,
        accentor: bool = True,
        accentor_type: str = "silero",
        yo_replacer: bool = False,
        enabled: bool = True
    ) -> "PipelineBuilder":
        """Configure text processing stage."""
        from src.pipeline.components import (
            SileroAccentorComponent,
            RuaccentComponent,
            RuleBasedYoReplacer,
            CompositeTextProcessor,
        )
        
        self._text_processing_enabled = enabled
        stage = TextProcessingStage(enabled=enabled)
        
        processors = []
        
        if accentor:
            if accentor_type == "ruaccent":
                processors.append(RuaccentComponent(enabled=enabled))
            else:
                processors.append(SileroAccentorComponent(enabled=enabled))
        
        if yo_replacer:
            processors.append(RuleBasedYoReplacer(enabled=enabled))
        
        if processors:
            stage.add_component(
                CompositeTextProcessor(processors=processors, enabled=enabled)
            )
        
        if processors:
            self._stages.append(stage)
        
        return self
    
    def with_voice_preparation(
        self,
        voice_sample_path: Optional[str] = None,
        use_stt: bool = True,
        enabled: bool = True
    ) -> "PipelineBuilder":
        """Configure voice preparation stage."""
        from src.pipeline.components import (
            VoiceLoaderComponent,
            STTTranscriberComponent,
        )
        
        self._voice_preparation_enabled = enabled
        stage = VoicePreparationStage(enabled=enabled)
        
        stage.add_component(
            VoiceLoaderComponent(
                voice_sample_path=voice_sample_path,
                enabled=enabled
            )
        )
        
        if use_stt:
            stage.add_component(STTTranscriberComponent(enabled=enabled))
        
        self._stages.append(stage)
        return self
    
    def with_tts(
        self,
        tts_engine,
        use_voice_clone: bool = True,
        enabled: bool = True
    ) -> "PipelineBuilder":
        """Configure TTS synthesis stage."""
        from src.pipeline.components import TTSComponent, TTSWithVoiceCloneComponent
        
        self._synthesis_enabled = enabled
        stage = SynthesisStage(enabled=enabled)
        
        if use_voice_clone:
            stage.add_component(
                TTSWithVoiceCloneComponent(tts_engine=tts_engine, enabled=enabled)
            )
        else:
            stage.add_component(TTSComponent(tts_engine=tts_engine, enabled=enabled))
        
        self._stages.append(stage)
        return self
    
    def with_voice_conversion(
        self,
        rvc_model_path: Optional[str] = None,
        pitch_adjustment: int = 0,
        enabled: bool = True
    ) -> "PipelineBuilder":
        """Configure voice conversion stage."""
        from src.pipeline.components import RVCComponent
        
        self._voice_conversion_enabled = enabled
        stage = VoiceConversionStage(enabled=enabled)
        
        stage.add_component(
            RVCComponent(
                rvc_model_path=rvc_model_path,
                pitch_adjustment=pitch_adjustment,
                enabled=enabled
            )
        )
        
        self._stages.append(stage)
        return self
    
    def with_publishing(
        self,
        publisher,
        enabled: bool = True
    ) -> "PipelineBuilder":
        """Configure publishing stage."""
        from src.pipeline.components import PublisherComponent
        
        self._publishing_enabled = enabled
        stage = PublishingStage(enabled=enabled)
        
        stage.add_component(PublisherComponent(publisher=publisher, enabled=enabled))
        self._stages.append(stage)
        return self
    
    # -------------------------------------------------------------------------
    # Build
    # -------------------------------------------------------------------------
    
    def build(self) -> Pipeline:
        """Build the Pipeline instance."""
        return Pipeline(stages=self._stages)
    
    def summary(self) -> str:
        """Get a summary of the pipeline configuration."""
        lines = ["Pipeline Configuration:", "─" * 40]
        
        enabled_stages = [s for s in self._stages if s.enabled]
        disabled_stages = [s for s in self._stages if not s.enabled]
        
        lines.append(f"Enabled stages ({len(enabled_stages)}):")
        for stage in enabled_stages:
            components = [c.name for c in stage.components if c.enabled]
            lines.append(f"  • {stage.name}: {', '.join(components) if components else 'no components'}")
        
        if disabled_stages:
            lines.append(f"\nDisabled stages ({len(disabled_stages)}):")
            for stage in disabled_stages:
                lines.append(f"  • {stage.name}")
        
        return "\n".join(lines)
