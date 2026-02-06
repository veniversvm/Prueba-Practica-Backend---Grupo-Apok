import re
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import Q

from nodes.models import Node # Importado para el conteo de nodos en DetailSerializer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer base para operaciones generales de lectura/actualización de usuarios.

    Campos clave:
    - 'password': WRITE_ONLY, requerido solo en creación/actualización de contraseña.
    - Campos de auditoría de nodos ('nodes_created_count' en DetailSerializer)
      se exponen como READ_ONLY.
    """
    password = serializers.CharField(
        write_only=True, 
        required=False, 
        style={'input_type': 'password'},
        help_text="Contraseña. Se ignora en el listado, requerida en el POST/PUT."
    )
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'is_email_confirmed', 'is_active', 'is_staff', 'is_superuser',
            'date_joined', 'last_login', 'password'
        ]
        read_only_fields = [
            'date_joined', 'last_login', 'is_staff', 'is_superuser'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True}
        }
    
    def validate_role(self, value):
        """
        Valida que solo usuarios SUDO puedan asignar el rol SUDO a otro usuario.
        """
        request = self.context.get('request')
        if request and value == 'SUDO':
            if request.user.role != 'SUDO':
                raise serializers.ValidationError(
                    "Solo los usuarios SUDO pueden asignar el rol SUDO."
                )
        return value
    
    def validate_email(self, value):
        """
        Valida la unicidad del email, permitiendo que la instancia actual mantenga el suyo.
        """
        if User.objects.filter(email__iexact=value).exists():
            if self.instance and self.instance.email.lower() == value.lower():
                return value  # Permite actualizar el email a sí mismo
            raise serializers.ValidationError("Este email ya está registrado.")
        return value
    
    def create(self, validated_data):
        """Crea un nuevo usuario con contraseña encriptada."""
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user
    
    def update(self, instance, validated_data):
        """Actualiza un usuario existente, manejando la contraseña si se proporciona."""
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance


class UserDetailSerializer(UserSerializer):
    """
    Serializer específico para la vista de detalle de usuario.
    Expone métricas de auditoría de nodos creados.
    """
    nodes_created_count = serializers.SerializerMethodField(
        help_text="Número total de nodos activos creados por este usuario."
    )
    
    class Meta(UserSerializer.Meta):
        # Añadimos el campo de conteo al listado de campos
        fields = UserSerializer.Meta.fields + ['nodes_created_count']
    
    def get_nodes_created_count(self, obj):
        """Calcula y retorna el número de nodos activos creados por el usuario."""
        return Node.objects.filter(created_by=obj, is_deleted=False).count()


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer específico para el registro de nuevos usuarios (POST /users/).
    Aplica validaciones estrictas de contraseña y rol durante la creación.
    """
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        style={'input_type': 'password'},
        min_length=8,
        help_text="Contraseña mínima de 8 caracteres."
    )
    password_confirm = serializers.CharField(
        write_only=True, 
        required=True, 
        style={'input_type': 'password'},
        help_text="Confirmación de la contraseña."
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'role', 'first_name', 'last_name']
    
    def validate(self, data):
        """Valida que las contraseñas coincidan antes de la validación de rol."""
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Las contraseñas no coinciden."})
        return data
    
    def validate_role(self, value):
        """Valida la restricción del rol SUDO al crear un nuevo usuario."""
        request = self.context.get('request')
        if request and value == 'SUDO':
            # El SUDO solo puede ser asignado por otro SUDO
            if request.user.role != 'SUDO':
                raise serializers.ValidationError("Solo los usuarios SUDO pueden crear otros usuarios SUDO.")
        return value
    
    def create(self, validated_data):
        """Crea el usuario, hashea la contraseña e inicializa is_email_confirmed a False."""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        # is_email_confirmed se establece a False por defecto en el modelo si no se pasa
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user