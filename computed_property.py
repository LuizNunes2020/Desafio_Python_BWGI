from functools import wraps

class computed_property:
    """
    Um decorador de propriedade computada com cache baseado em atributos dependentes.
    O valor da propriedade é recomputado apenas quando algum dos atributos declarados muda.
    Suporta getter, setter, deleter e preserva docstring como `property`.
    """
    __slots__ = (
        'dependencies', '_func', '_getter', '_setter', '_deleter',
        'name', '_attr_name', '_state_name'
    )


    def __init__(self, *dependencies):
        """
        Inicializa a propriedade computada com os nomes dos atributos dependentes.
        """
        self.dependencies = set(dep.strip() for dep in dependencies)
        self._func = None
        self._getter = None
        self._setter = None
        self._deleter = None
        self.name = None
        self._attr_name = None
        self._state_name = None
        self.__doc__ = None

    def __call__(self, func):
        """
        Chamado quando o método é decorado. Armazena a função original e define o getter com cache.
        """
        self._func = func
        self.__doc__ = func.__doc__  # Preserva a docstring para uso no help()

        @wraps(func)
        def getter(instance):
            # Obtém o estado atual das dependências
            current_state = tuple(getattr(instance, dep, None) for dep in self.dependencies)
            # Verifica o último estado armazenado
            last_state = getattr(instance, self._state_name, None)

            # Se qualquer dependência mudou, recomputa
            if last_state != current_state:
                value = self._func(instance)
                object.__setattr__(instance, self._attr_name, value)
                object.__setattr__(instance, self._state_name, current_state)

            # Retorna o valor cacheado
            return getattr(instance, self._attr_name)

        self._getter = getter
        return self

    def __set_name__(self, owner, name):
        """
        Chamado automaticamente pelo Python quando o descritor é atribuído a uma classe.
        Define os nomes internos de cache com base no nome do atributo.
        """
        self.name = name
        self._attr_name = f"_cached_{name}"
        self._state_name = f"_state_{name}"

    def __get__(self, instance, owner):
        """
        Retorna o valor da propriedade computada, chamando o getter com cache.
        """
        if instance is None:
            return self  # Retorna o descritor se chamado pela classe
        return self._getter(instance)

    def setter(self, func):
        """
        Permite definir um setter com @<prop>.setter.
        """
        self._setter = func
        return self

    def deleter(self, func):
        """
        Permite definir um deleter com @<prop>.deleter.
        """
        self._deleter = func
        return self

    def _invalidate_cache(self, instance):
        """
        Invalida o valor cacheado e o estado anterior, forçando recomputação futura.
        """
        for attr in (self._attr_name, self._state_name):
            if hasattr(instance, attr):
                delattr(instance, attr)

    def __set__(self, instance, value):
        """
        Define um novo valor via setter, se disponível. Invalida o cache.
        """
        if self._setter is None:
            raise AttributeError("can't set attribute")
        self._setter(instance, value)
        self._invalidate_cache(instance)

    def __delete__(self, instance):
        """
        Deleta o valor via deleter, se disponível. Invalida o cache.
        """
        if self._deleter is None:
            raise AttributeError("can't delete attribute")
        self._deleter(instance)
        self._invalidate_cache(instance)