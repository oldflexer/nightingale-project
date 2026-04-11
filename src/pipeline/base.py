"""
Базовые классы для компонентов и стадий pipeline.
"""
from abc import ABC, abstractmethod
from typing import Optional

from loguru import logger

from src.pipeline.context import PipelineContext


class PipelineComponent(ABC):
    """
    Базовый класс для всех компонентов pipeline.
    
    Каждый компонент:
    - Имеет уникальное имя для логирования
    - Может быть включен/выключен
    - Может выполнять setup/teardown
    - Обрабатывает PipelineContext
    
    Example:
        class MyComponent(PipelineComponent):
            @property
            def name(self) -> str:
                return "my_component"
            
            def process(self, context: PipelineContext) -> PipelineContext:
                # Process context
                return context
    """
    
    def __init__(self, name: str, enabled: bool = True):
        self._name = name
        self._enabled = enabled
        self._logger = logger.bind(component=name)
    
    @property
    def name(self) -> str:
        """Component name for logging."""
        return self._name
    
    @property
    def enabled(self) -> bool:
        """Whether component is active."""
        return self._enabled
    
    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value
        self._logger.info(f"Component {'enabled' if value else 'disabled'}")
    
    @property
    def logger(self):
        """Logger bound to component name."""
        return self._logger
    
    @abstractmethod
    def process(self, context: PipelineContext) -> PipelineContext:
        """
        Обработать контекст и вернуть обновленный контекст.
        
        Args:
            context: Текущий контекст pipeline
            
        Returns:
            Обновленный контекст
        """
        pass
    
    def setup(self) -> None:
        """
        Опциональный метод инициализации.
        Вызывается один раз перед началом pipeline.
        """
        pass
    
    def teardown(self) -> None:
        """
        Опциональный метод очистки.
        Вызывается после завершения pipeline.
        """
        pass
    
    def _skip(self, context: PipelineContext) -> PipelineContext:
        """Helper to skip processing and return context unchanged."""
        self._logger.debug("Component skipped (disabled)")
        return context
    
    def _validate_context(
        self,
        context: PipelineContext,
        required_fields: list[str],
    ) -> bool:
        """
        Validate that context has required fields populated.
        Returns True if valid, logs error and adds to context if not.
        """
        missing = []
        for field in required_fields:
            value = getattr(context, field, None)
            if value is None or (isinstance(value, str) and not value):
                missing.append(field)
        
        if missing:
            self._logger.error(f"Missing required context fields: {missing}")
            context.add_error(f"{self._name}: missing fields {missing}")
            return False
        return True


class Stage(ABC):
    """
    Стадия pipeline - логическая группа компонентов.
    
    Стадия:
    - Имеет имя для логирования
    - Содержит список компонентов
    - Выполняет компоненты последовательно
    - Может быть включена/выключена
    
    Example:
        class MyStage(Stage):
            @property
            def name(self) -> str:
                return "my_stage"
            
            @property
            def components(self) -> list[PipelineComponent]:
                return [self.component1, self.component2]
    """
    
    def __init__(self, name: str, enabled: bool = True):
        self._name = name
        self._enabled = enabled
        self._logger = logger.bind(stage=name)
        self._components: list[PipelineComponent] = []
    
    @property
    def name(self) -> str:
        """Stage name for logging."""
        return self._name
    
    @property
    def enabled(self) -> bool:
        """Whether stage is active."""
        return self._enabled
    
    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value
        self._logger.info(f"Stage {'enabled' if value else 'disabled'}")
    
    @property
    def logger(self):
        """Logger bound to stage name."""
        return self._logger
    
    @property
    def components(self) -> list[PipelineComponent]:
        """List of components in this stage."""
        return self._components
    
    def add_component(self, component: PipelineComponent) -> "Stage":
        """Add component to stage. Returns self for chaining."""
        self._components.append(component)
        return self
    
    def execute(self, context: PipelineContext) -> PipelineContext:
        """
        Выполнить все включенные компоненты стадии.
        
        Args:
            context: Текущий контекст pipeline
            
        Returns:
            Обновленный контекст
        """
        if not self._enabled:
            self._logger.info("Stage skipped (disabled)")
            return context
        
        enabled_components = [c for c in self._components if c.enabled]
        
        if not enabled_components:
            self._logger.debug("No enabled components in stage")
            return context
        
        self._logger.info(
            f"Stage started with {len(enabled_components)} component(s)"
        )
        
        for component in enabled_components:
            self._logger.debug(f"Running component '{component.name}'...")
            try:
                context = component.process(context)
                self._logger.debug(f"Component '{component.name}' completed")
            except Exception as e:
                self._logger.exception(
                    f"Component '{component.name}' failed: {e}"
                )
                context.add_error(
                    f"Stage '{self._name}': Component '{component.name}' failed: {e}"
                )
                return context
        
        self._logger.info("Stage completed successfully")
        return context
    
    def setup(self) -> None:
        """Setup all components in stage."""
        self._logger.debug("Setting up stage...")
        for component in self._components:
            if component.enabled:
                try:
                    component.setup()
                except Exception as e:
                    self._logger.warning(
                        f"Component '{component.name}' setup failed: {e}"
                    )
    
    def teardown(self) -> None:
        """Teardown all components in stage."""
        self._logger.debug("Tearing down stage...")
        for component in self._components:
            if component.enabled:
                try:
                    component.teardown()
                except Exception as e:
                    self._logger.warning(
                        f"Component '{component.name}' teardown failed: {e}"
                    )
