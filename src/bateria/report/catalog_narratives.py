"""Catálogo clínico de dimensiones, dominios y baremos (Villalobos / MinTrabajo).

Textos en registro profesional SST. No se generan con LLM en runtime:
el informe interpola estas plantillas con las cifras de la medición.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

# Código estable → nombre oficial
CODIGOS_DIMENSION: Dict[str, str] = {
    "Demandas ambientales y de esfuerzo físico": "INTRA_AMB",
    "Demandas cuantitativas": "INTRA_CUA",
    "Demandas de carga mental": "INTRA_MEN",
    "Exigencias de responsabilidad del cargo": "INTRA_RES",
    "Consistencia del rol": "INTRA_CON",
    "Demandas de la jornada de trabajo": "INTRA_JOR",
    "Influencia del trabajo sobre el entorno extralaboral": "INTRA_INF",
    "Oportunidades para el uso y desarrollo de habilidades y conocimientos": "INTRA_HAB",
    "Control y autonomía sobre el trabajo": "INTRA_AUT",
    "Participación y manejo del cambio": "INTRA_CAM",
    "Claridad de rol": "INTRA_CLA",
    "Capacitación": "INTRA_CAP",
    "Características del liderazgo": "INTRA_LID",
    "Relaciones sociales en el trabajo": "INTRA_REL",
    "Retroalimentación del desempeño": "INTRA_RET",
    "Relación con los colaboradores": "INTRA_COL",
    "Demandas emocionales": "INTRA_EMO",
    "Recompensas derivadas de la pertenencia a la organización y del trabajo que se realiza": "INTRA_PER",
    "Reconocimiento y compensación": "INTRA_REC",
    "Tiempo fuera del trabajo": "EXTRA_TFT",
    "Relaciones familiares": "EXTRA_FAM",
    "Comunicación y relaciones interpersonales": "EXTRA_COM",
    "Situación económica del grupo familiar": "EXTRA_ECO",
    "Características de la vivienda y de su entorno": "EXTRA_VIV",
    "Influencia del entorno extralaboral sobre el trabajo": "EXTRA_INF",
    "Desplazamiento vivienda-trabajo-vivienda": "EXTRA_DES",
    "Síntomas de estrés": "ESTRES_SIN",
}

CODIGOS_DOMINIO: Dict[str, str] = {
    "Liderazgo y relaciones sociales en el trabajo": "DOM_LID",
    "Control sobre el trabajo": "DOM_CON",
    "Demandas del trabajo": "DOM_DEM",
    "Recompensas": "DOM_REC",
}

CODIGOS_TOTAL: Dict[str, str] = {
    "intra": "INTRA_TOTAL",
    "extra": "EXTRA_TOTAL",
    "estres": "ESTRES_TOTAL",
    "general": "GENERAL_TOTAL",
}

# Orden de presentación en el informe (Forma A completa; Forma B omite algunas).
ORDEN_INTRA = [
    "Características del liderazgo",
    "Relaciones sociales en el trabajo",
    "Retroalimentación del desempeño",
    "Relación con los colaboradores",
    "Claridad de rol",
    "Capacitación",
    "Participación y manejo del cambio",
    "Oportunidades para el uso y desarrollo de habilidades y conocimientos",
    "Control y autonomía sobre el trabajo",
    "Demandas ambientales y de esfuerzo físico",
    "Demandas emocionales",
    "Demandas cuantitativas",
    "Influencia del trabajo sobre el entorno extralaboral",
    "Exigencias de responsabilidad del cargo",
    "Demandas de carga mental",
    "Consistencia del rol",
    "Demandas de la jornada de trabajo",
    "Recompensas derivadas de la pertenencia a la organización y del trabajo que se realiza",
    "Reconocimiento y compensación",
]

ORDEN_EXTRA = [
    "Tiempo fuera del trabajo",
    "Relaciones familiares",
    "Comunicación y relaciones interpersonales",
    "Situación económica del grupo familiar",
    "Características de la vivienda y de su entorno",
    "Influencia del entorno extralaboral sobre el trabajo",
    "Desplazamiento vivienda-trabajo-vivienda",
]

ORDEN_DOMINIOS = [
    "Liderazgo y relaciones sociales en el trabajo",
    "Control sobre el trabajo",
    "Demandas del trabajo",
    "Recompensas",
]


def codigo_de(nombre: str, instrumento: str = "intra") -> str:
    if nombre in CODIGOS_DIMENSION:
        return CODIGOS_DIMENSION[nombre]
    if nombre in CODIGOS_DOMINIO:
        return CODIGOS_DOMINIO[nombre]
    if instrumento in CODIGOS_TOTAL:
        return CODIGOS_TOTAL[instrumento]
    return f"{instrumento.upper()}_{nombre[:24].upper().replace(' ', '_')}"


# Cada entrada: definicion, interpretacion_alto, intervencion_primaria, intervencion_secundaria, instrumento, dominio
NARRATIVAS: Dict[str, Dict[str, str]] = {
    "Características del liderazgo": {
        "instrumento": "intra",
        "dominio": "Liderazgo y relaciones sociales en el trabajo",
        "definicion": (
            "Evalúa la gestión del jefe inmediato: comunicación, trato respetuoso, "
            "orientación técnica, reconocimiento del trabajo y resolución de dificultades. "
            "Un liderazgo de baja calidad se asocia con clima tenso, desmotivación y quejas reiteradas."
        ),
        "interpretacion_alto": (
            "La concentración en riesgo alto o muy alto indica que una fracción relevante de la planta "
            "percibe jefaturas distantes, poco claras o inequitativas. Este patrón suele anteceder "
            "conflictos, rotación y quejas por acoso o trato indigno, y debe priorizarse en el PVE."
        ),
        "intervencion_primaria": (
            "Formar a jefaturas en liderazgo saludable, retroalimentación no punitiva y comunicación "
            "bidireccional; publicar un protocolo de trato digno y canales de escalamiento."
        ),
        "intervencion_secundaria": (
            "Coaching individual a jefes de las áreas críticas, grupos focales de clima y seguimiento "
            "trimestral del dominio de liderazgo."
        ),
    },
    "Relaciones sociales en el trabajo": {
        "instrumento": "intra",
        "dominio": "Liderazgo y relaciones sociales en el trabajo",
        "definicion": (
            "Mide cohesión, apoyo entre compañeros, posibilidad de colaboración y calidad de las "
            "relaciones en el grupo de trabajo. Incluye, en Forma A, ítems de relación con pares de otras áreas."
        ),
        "interpretacion_alto": (
            "Riesgo alto sugiere aislamiento, rivalidad o falta de apoyo social. Es un predictor de "
            "malestar emocional, errores por falta de cooperación y deterioro del trabajo en equipo."
        ),
        "intervencion_primaria": (
            "Diseñar espacios formales de cooperación (reuniones de equipo, rituales de reconocimiento "
            "entre pares) y normas claras contra el hostigamiento entre compañeros."
        ),
        "intervencion_secundaria": (
            "Intervención de clima en las áreas afectadas y mediación de conflictos recurrentes."
        ),
    },
    "Retroalimentación del desempeño": {
        "instrumento": "intra",
        "dominio": "Liderazgo y relaciones sociales en el trabajo",
        "definicion": (
            "Valora si la persona recibe información oportuna, específica y útil sobre la calidad de "
            "su trabajo, de modo que pueda corregir y mejorar."
        ),
        "interpretacion_alto": (
            "La ausencia de retroalimentación genera incertidumbre, sensación de injusticia y baja "
            "autoeficacia. En cargos operativos se traduce en retrabajo y en cargos profesionales, en desmotivación."
        ),
        "intervencion_primaria": (
            "Implantar ciclos de retroalimentación (semanal/quincenal) con criterios observables, "
            "no solo la evaluación anual."
        ),
        "intervencion_secundaria": (
            "Entrenar a jefes en feedback efectivo y revisar el sistema de evaluación de desempeño."
        ),
    },
    "Relación con los colaboradores": {
        "instrumento": "intra",
        "dominio": "Liderazgo y relaciones sociales en el trabajo",
        "definicion": (
            "Dimensión opcional de Forma A, aplicable a quienes tienen personal a cargo. Explora la "
            "calidad de la relación del jefe con su equipo (respeto, cooperación, dificultades de supervisión)."
        ),
        "interpretacion_alto": (
            "Riesgo alto en jefaturas señala sobrecarga de supervisión, equipos difíciles o falta de "
            "herramientas de gestión de personas. Requiere intervención tanto sobre el jefe como sobre el grupo."
        ),
        "intervencion_primaria": (
            "Aclarar span de control, apoyar con herramientas de supervisión y alinear expectativas de rol de jefe."
        ),
        "intervencion_secundaria": (
            "Acompañamiento a jefes nuevos y revisión de cargas de personal a cargo."
        ),
    },
    "Claridad de rol": {
        "instrumento": "intra",
        "dominio": "Control sobre el trabajo",
        "definicion": (
            "Determina si la persona conoce sus funciones, el margen de autoridad, los resultados "
            "esperados y los procedimientos para cumplir el cargo."
        ),
        "interpretacion_alto": (
            "La ambigüedad de rol es un estresor clásico: duplicidad de órdenes, tareas no descritas "
            "y responsabilidad sin autoridad. Se asocia con errores, conflicto interpersonal y desgaste."
        ),
        "intervencion_primaria": (
            "Actualizar descriptores de cargo, matrices RACI y procesos de inducción; comunicar cambios de rol por escrito."
        ),
        "intervencion_secundaria": (
            "Talleres de claridad de rol por área y conciliación de funciones solapadas entre cargos."
        ),
    },
    "Capacitación": {
        "instrumento": "intra",
        "dominio": "Control sobre el trabajo",
        "definicion": (
            "Evalúa si la organización proporciona formación suficiente, pertinente y oportuna para "
            "desempeñar el cargo con seguridad y calidad."
        ),
        "interpretacion_alto": (
            "Déficit de capacitación se traduce en inseguridad técnica, improvisación y exposición a "
            "error. En SST también incrementa el riesgo de incidente por desconocimiento."
        ),
        "intervencion_primaria": (
            "Plan de formación por competencia del cargo, con inducción reforzada y reentrenamiento periódico."
        ),
        "intervencion_secundaria": (
            "Cerrar brechas detectadas en las áreas con mayor % crítico y evaluar eficacia de la formación."
        ),
    },
    "Participación y manejo del cambio": {
        "instrumento": "intra",
        "dominio": "Control sobre el trabajo",
        "definicion": (
            "Mide si las personas son consultadas o informadas sobre cambios que afectan su trabajo, "
            "y si existe un manejo ordenado de las transiciones organizacionales."
        ),
        "interpretacion_alto": (
            "Cambios impuestos sin explicación generan resistencia, rumores y pérdida de control percibido, "
            "elevando el estrés y la rotación en periodos de reestructuración."
        ),
        "intervencion_primaria": (
            "Protocolo de gestión del cambio: anuncio, justificación, participación representativa y seguimiento."
        ),
        "intervencion_secundaria": (
            "Mesas de cambio en las unidades afectadas y comunicación bidireccional durante la transición."
        ),
    },
    "Oportunidades para el uso y desarrollo de habilidades y conocimientos": {
        "instrumento": "intra",
        "dominio": "Control sobre el trabajo",
        "definicion": (
            "Valora si el trabajo permite aplicar y desarrollar conocimientos, creatividad e iniciativa, "
            "o si se limita a tareas rutinarias sin aprendizaje."
        ),
        "interpretacion_alto": (
            "La subutilización de habilidades produce aburrimiento, desapego y fuga de talento; en el "
            "otro extremo, exigir habilidades no formadas produce sobrecarga cognitiva."
        ),
        "intervencion_primaria": (
            "Enriquecer puestos (rotación planificada, proyectos de mejora, planes de carrera) alineados al cargo."
        ),
        "intervencion_secundaria": (
            "Identificar personas con alto potencial subutilizado y reasignar funciones con tutoría."
        ),
    },
    "Control y autonomía sobre el trabajo": {
        "instrumento": "intra",
        "dominio": "Control sobre el trabajo",
        "definicion": (
            "Explora el margen para decidir el orden, el ritmo y los métodos de trabajo. El modelo "
            "demanda-control (Karasek) predice mayor tensión cuando hay alta demanda y bajo control."
        ),
        "interpretacion_alto": (
            "Baja autonomía con altas demandas es el patrón de mayor riesgo psicofisiológico. Se observa "
            "en líneas rígidas, micromanagement y procedimientos que no admiten criterio profesional."
        ),
        "intervencion_primaria": (
            "Aumentar discrecionalidad donde el riesgo lo permita; eliminar controles redundantes y "
            "definir resultados, no solo procedimientos."
        ),
        "intervencion_secundaria": (
            "Revisión ergonómica de flujos y acuerdos de autonomía por equipo."
        ),
    },
    "Demandas ambientales y de esfuerzo físico": {
        "instrumento": "intra",
        "dominio": "Demandas del trabajo",
        "definicion": (
            "Condiciones del puesto: ruido, iluminación, temperatura, espacio, herramientas y esfuerzo "
            "físico. Interactúan con el riesgo psicosocial al aumentar la fatiga y la irritabilidad."
        ),
        "interpretacion_alto": (
            "Ambientes deficientes o esfuerzo físico excesivo elevan la carga alostática y potencian "
            "el malestar de otras dimensiones (jornada, demandas cuantitativas)."
        ),
        "intervencion_primaria": (
            "Inspecciones de higiene industrial, pausas activas, dotación adecuada y mantenimiento de equipos."
        ),
        "intervencion_secundaria": (
            "Ajustes de puesto para trabajadores con fatiga crónica y seguimiento médico ocupacional."
        ),
    },
    "Demandas emocionales": {
        "instrumento": "intra",
        "dominio": "Demandas del trabajo",
        "definicion": (
            "Exposición a sufrimiento ajeno, agresión de usuarios, exigencia de ocultar emociones o "
            "atención a público difícil. Incluye, cuando aplica, ítems de servicio al cliente."
        ),
        "interpretacion_alto": (
            "Alta demanda emocional sin recursos de afrontamiento predice burnout, síntomas ansiosos "
            "y rotación en cargos de atención. Requiere contención institucional, no solo resiliencia individual."
        ),
        "intervencion_primaria": (
            "Protocolos de atención a usuarios agresivos, rotación de exposición y formación en regulación emocional."
        ),
        "intervencion_secundaria": (
            "Espacios de descarga profesional supervisada y ruta de atención psicológica para casos sintomáticos."
        ),
    },
    "Demandas cuantitativas": {
        "instrumento": "intra",
        "dominio": "Demandas del trabajo",
        "definicion": (
            "Cantidad de trabajo en relación con el tiempo disponible: acumulación de tareas, ritmos "
            "imposibles y sensación de no alcanzar a terminar."
        ),
        "interpretacion_alto": (
            "Sobrecarga cuantitativa es de las dimensiones más asociadas a estrés agudo, errores y "
            "trabajo en casa no remunerado. Debe cruzarse con jornada y con indicadores de productividad."
        ),
        "intervencion_primaria": (
            "Balancear cargas, fijar cupos máximos, eliminar tareas de bajo valor y dimensionar plantillas."
        ),
        "intervencion_secundaria": (
            "Auditoría de tiempos en las áreas críticas y acuerdos de no disponibilidad fuera de jornada."
        ),
    },
    "Influencia del trabajo sobre el entorno extralaboral": {
        "instrumento": "intra",
        "dominio": "Demandas del trabajo",
        "definicion": (
            "Grado en que el trabajo invade familia, descanso y vida personal (llevarse preocupaciones, "
            "trabajo en casa, dificultad para desconectar)."
        ),
        "interpretacion_alto": (
            "La interferencia trabajo-familia es un mediador entre demandas laborales y síntomas de estrés. "
            "Se agrava con conectividad permanente y jornadas extendidas."
        ),
        "intervencion_primaria": (
            "Política de desconexión laboral, límites de correo fuera de horario y respeto del descanso."
        ),
        "intervencion_secundaria": (
            "Acompañamiento a cargos con guardias o disponibilidad 24/7 y revisión de turnos."
        ),
    },
    "Exigencias de responsabilidad del cargo": {
        "instrumento": "intra",
        "dominio": "Demandas del trabajo",
        "definicion": (
            "Dimensión de Forma A. Valora la responsabilidad sobre bienes, información, seguridad de "
            "otros o resultados de alto impacto, y si esa responsabilidad es proporcional a los recursos."
        ),
        "interpretacion_alto": (
            "Responsabilidad alta sin autoridad ni recursos produce tensión crónica en jefaturas y "
            "profesionales. No se resuelve con 'fortaleza', sino con rediseño del cargo."
        ),
        "intervencion_primaria": (
            "Alinear responsabilidad con autoridad, seguros y respaldos técnicos; clarificar límites de decisión."
        ),
        "intervencion_secundaria": (
            "Supervisión de apoyo (no punitiva) para cargos de alta responsabilidad."
        ),
    },
    "Demandas de carga mental": {
        "instrumento": "intra",
        "dominio": "Demandas del trabajo",
        "definicion": (
            "Esfuerzo cognitivo: atención sostenida, memoria, decisiones simultáneas, información compleja. "
            "Los baremos de esta dimensión son exigentes: puntajes altos son frecuentes y deben interpretarse con el corte oficial."
        ),
        "interpretacion_alto": (
            "Carga mental elevada es esperable en cargos técnicos; el riesgo aparece cuando se combina "
            "con baja autonomía, interrupciones constantes o jornadas largas."
        ),
        "intervencion_primaria": (
            "Diseño de puestos que reduzcan interrupciones, ayudas a la decisión y pausas cognitivas."
        ),
        "intervencion_secundaria": (
            "Entrenamiento en gestión de atención y revisión de sistemas de información poco usables."
        ),
    },
    "Consistencia del rol": {
        "instrumento": "intra",
        "dominio": "Demandas del trabajo",
        "definicion": (
            "Dimensión de Forma A. Detecta contradicciones: órdenes opuestas, procedimientos que impiden "
            "cumplir la función, o valores organizacionales en conflicto con la tarea diaria."
        ),
        "interpretacion_alto": (
            "El conflicto de rol es un estresor fuerte y poco visible. Se manifiesta como cinismo, "
            "incumplimiento de normas y desgaste moral."
        ),
        "intervencion_primaria": (
            "Auditar procedimientos vs. práctica real; eliminar metas contradictorias (p. ej. calidad vs. velocidad sin prioridad)."
        ),
        "intervencion_secundaria": (
            "Mesas de consistencia de rol entre áreas que se envían órdenes cruzadas."
        ),
    },
    "Demandas de la jornada de trabajo": {
        "instrumento": "intra",
        "dominio": "Demandas del trabajo",
        "definicion": (
            "Duración, horarios, turnos, trabajo dominical o nocturno y posibilidad de pausas. "
            "Se relaciona con fatiga, sueño y vida familiar."
        ),
        "interpretacion_alto": (
            "Jornadas extendidas o turnos mal diseñados elevan síntomas fisiológicos de estrés y "
            "accidentes. Deben verificarse frente a la normativa de jornada máxima."
        ),
        "intervencion_primaria": (
            "Cumplir jornada legal, rotación de turnos saludable, horas extra controladas y pausas reales."
        ),
        "intervencion_secundaria": (
            "Vigilancia de fatiga en turnos nocturnos y ajuste de dotación en picos de demanda."
        ),
    },
    "Recompensas derivadas de la pertenencia a la organización y del trabajo que se realiza": {
        "instrumento": "intra",
        "dominio": "Recompensas",
        "definicion": (
            "Orgullo de pertenecer, sentido del trabajo y percepción de que la organización valora "
            "a las personas más allá del salario."
        ),
        "interpretacion_alto": (
            "Baja recompensa de pertenencia predice desapego y retiro psicológico. En el modelo "
            "esfuerzo-recompensa (Siegrist) potencia el riesgo cuando el esfuerzo es alto."
        ),
        "intervencion_primaria": (
            "Comunicar propósito, reconocer logros colectivos y hacer visible el impacto del trabajo de cada área."
        ),
        "intervencion_secundaria": (
            "Planes de cultura y encuestas de sentido de pertenencia en las unidades críticas."
        ),
    },
    "Reconocimiento y compensación": {
        "instrumento": "intra",
        "dominio": "Recompensas",
        "definicion": (
            "Percepción de equidad en el reconocimiento del desempeño, las posibilidades de promoción "
            "y la compensación (no solo salarial: también prestigio y trato)."
        ),
        "interpretacion_alto": (
            "Inequidad percibida es un potente predictor de malestar, quejas y rotación. Debe leerse "
            "junto con liderazgo y recompensas de pertenencia."
        ),
        "intervencion_primaria": (
            "Criterios transparentes de reconocimiento, revisión de equidad interna y no reducir el reconocimiento al bono."
        ),
        "intervencion_secundaria": (
            "Ajustes puntuales de compensación en cargos con brecha demostrada y reconocimiento no monetario sistemático."
        ),
    },
    "Tiempo fuera del trabajo": {
        "instrumento": "extra",
        "dominio": "Extralaboral",
        "definicion": (
            "Disponibilidad de tiempo para descanso, familia, estudio y ocio. Un tiempo insuficiente "
            "impide la recuperación y mantiene activado el eje de estrés."
        ),
        "interpretacion_alto": (
            "Poco tiempo fuera del trabajo, unido a jornadas largas o doble jornada doméstica, "
            "eleva síntomas de estrés y deteriora la conciliación."
        ),
        "intervencion_primaria": (
            "Promover uso real de vacaciones, pausas y jornadas que permitan recuperación; orientar sobre conciliación."
        ),
        "intervencion_secundaria": (
            "Identificar grupos con doble carga (cuidado de otros) y ofrecer horarios flexibles cuando el proceso lo permita."
        ),
    },
    "Relaciones familiares": {
        "instrumento": "extra",
        "dominio": "Extralaboral",
        "definicion": (
            "Calidad del apoyo y las relaciones en el grupo familiar. Es un recurso extralaboral "
            "que amortigua o agrava el impacto de las demandas del trabajo."
        ),
        "interpretacion_alto": (
            "Dificultades familiares no son 'problema privado' cuando impactan el desempeño y la salud. "
            "La intervención es de orientación y ruta de apoyo, no de invasión de la intimidad."
        ),
        "intervencion_primaria": (
            "Orientación a la familia trabajadora, programa de asistencia al empleado y respeto a la reserva de datos."
        ),
        "intervencion_secundaria": (
            "Remisión voluntaria a apoyo psicológico o trabajo social según necesidad identificada."
        ),
    },
    "Comunicación y relaciones interpersonales": {
        "instrumento": "extra",
        "dominio": "Extralaboral",
        "definicion": (
            "Red de apoyo social fuera del trabajo: amigos, vecinos, posibilidad de conversar y "
            "recibir ayuda. Complementa las relaciones familiares."
        ),
        "interpretacion_alto": (
            "Aislamiento social extralaboral reduce la capacidad de afrontamiento y se asocia con "
            "mayor sintomatología depresiva y de estrés."
        ),
        "intervencion_primaria": (
            "Fomentar espacios de integración voluntaria y grupos de interés, sin hacerlos obligatorios."
        ),
        "intervencion_secundaria": (
            "Ruta de apoyo para trabajadores con red social escasa y signos de aislamiento."
        ),
    },
    "Situación económica del grupo familiar": {
        "instrumento": "extra",
        "dominio": "Extralaboral",
        "definicion": (
            "Suficiencia de los ingresos para cubrir necesidades del hogar. El estrés económico "
            "se traslada al trabajo en forma de preocupación, ausentismo y menor concentración."
        ),
        "interpretacion_alto": (
            "Riesgo alto aquí no se 'resuelve' con talleres de actitud. Requiere revisar compensación, "
            "educación financiera y, cuando aplique, fondos de calamidad."
        ),
        "intervencion_primaria": (
            "Educación financiera, revisión de equidad salarial y beneficios que cubran necesidades básicas."
        ),
        "intervencion_secundaria": (
            "Orientación individual confidencial y alianzas con cajas de compensación."
        ),
    },
    "Características de la vivienda y de su entorno": {
        "instrumento": "extra",
        "dominio": "Extralaboral",
        "definicion": (
            "Condiciones de la vivienda (espacio, servicios, ruido, seguridad del barrio) que afectan "
            "el descanso y la recuperación."
        ),
        "interpretacion_alto": (
            "Vivienda inadecuada o entorno inseguro impide el descanso y mantiene alerta permanente. "
            "La empresa interviene con orientación y, si existe, auxilios de vivienda, no con juicios morales."
        ),
        "intervencion_primaria": (
            "Informar beneficios de vivienda y cajas de compensación; considerar teletrabajo solo si la vivienda lo permite."
        ),
        "intervencion_secundaria": (
            "Remisión a programas sociales cuando el trabajador lo autorice."
        ),
    },
    "Influencia del entorno extralaboral sobre el trabajo": {
        "instrumento": "extra",
        "dominio": "Extralaboral",
        "definicion": (
            "Problemas del entorno personal que interfieren con el cumplimiento del trabajo "
            "(preocupaciones, responsabilidades de cuidado, situaciones legales o de salud familiar)."
        ),
        "interpretacion_alto": (
            "Alta interferencia extra→trabajo exige políticas de flexibilidad y apoyo, no sanción. "
            "De lo contrario se cronifica el ausentismo y el presentismo."
        ),
        "intervencion_primaria": (
            "Permisos por calamidad claros, horarios flexibles razonables y jefes entrenados en apoyo no estigmatizante."
        ),
        "intervencion_secundaria": (
            "Acompañamiento caso a caso por SST y talento humano, con reserva de la información."
        ),
    },
    "Desplazamiento vivienda-trabajo-vivienda": {
        "instrumento": "extra",
        "dominio": "Extralaboral",
        "definicion": (
            "Tiempo, medio y condiciones del trayecto diario. Un desplazamiento largo o inseguro "
            "es tiempo no recuperado y fuente de fatiga antes de iniciar la jornada."
        ),
        "interpretacion_alto": (
            "Trayectos prolongados se asocian con menor tiempo de sueño y mayor estrés. Es un factor "
            "estructural: se interviene con horarios, transporte o ubicación, no con 'actitud positiva'."
        ),
        "intervencion_primaria": (
            "Horarios escalonados, rutas de transporte, teletrabajo híbrido cuando el proceso lo permita."
        ),
        "intervencion_secundaria": (
            "Priorizar ajustes de horario en quienes reportan trayectos de muy alto riesgo."
        ),
    },
    "Síntomas de estrés": {
        "instrumento": "estres",
        "dominio": "Estrés",
        "definicion": (
            "El Cuestionario de Estrés (3.ª versión, 31 ítems) indaga malestares fisiológicos, de "
            "comportamiento social, intelectuales y psicoemocionales. Escala 0–3; ningún ítem se invierte: "
            "'Siempre' puntúa máximo riesgo."
        ),
        "interpretacion_alto": (
            "Un porcentaje alto en riesgo alto o muy alto indica sintomatología que ya rebasa el malestar "
            "adaptativo. No sustituye diagnóstico clínico, pero obliga a ruta de atención y a intervenir "
            "las dimensiones intra/extra que lo alimentan."
        ),
        "intervencion_primaria": (
            "PVE con vigilancia de síntomas, pausas, higiene de sueño y control de las demandas laborales identificadas."
        ),
        "intervencion_secundaria": (
            "Ruta de atención psicológica/médica ocupacional para casos en riesgo alto y muy alto, con consentimiento informado."
        ),
        "intervencion_terciaria": (
            "Reincorporación protegida, ajuste de puesto y seguimiento de trabajadores con cuadro clínico documentado."
        ),
    },
    "Liderazgo y relaciones sociales en el trabajo": {
        "instrumento": "intra",
        "dominio": "Liderazgo y relaciones sociales en el trabajo",
        "definicion": (
            "Dominio que agrupa liderazgo, relaciones sociales, retroalimentación y, cuando aplica, "
            "relación con colaboradores. Es el principal predictor de clima y de quejas por trato."
        ),
        "interpretacion_alto": (
            "Riesgo concentrado en este dominio exige intervención sobre jefaturas y normas de convivencia, "
            "no solo sobre el trabajador."
        ),
        "intervencion_primaria": (
            "Programa de liderazgo saludable y política de convivencia laboral (Ley 1010)."
        ),
        "intervencion_secundaria": (
            "Intervención de clima por áreas y seguimiento COPASST / comité de convivencia."
        ),
    },
    "Control sobre el trabajo": {
        "instrumento": "intra",
        "dominio": "Control sobre el trabajo",
        "definicion": (
            "Agrupa claridad de rol, capacitación, participación en el cambio, uso de habilidades y autonomía. "
            "Es el recurso que equilibra las demandas."
        ),
        "interpretacion_alto": (
            "Bajo control con altas demandas es el escenario de mayor tensión. La intervención es de rediseño del trabajo."
        ),
        "intervencion_primaria": (
            "Clarificar roles, formar y devolver autonomía operativa."
        ),
        "intervencion_secundaria": (
            "Rediseño de puestos en las unidades con peor puntaje de control."
        ),
    },
    "Demandas del trabajo": {
        "instrumento": "intra",
        "dominio": "Demandas del trabajo",
        "definicion": (
            "Agrupa carga cuantitativa, mental, emocional, ambiental, jornada, consistencia e influencia "
            "sobre la vida personal. Es el dominio de 'cuánto pesa el trabajo'."
        ),
        "interpretacion_alto": (
            "Demandas altas sostenidas, sin recuperación, producen fatiga y síntomas. Hay que bajar carga "
            "o subir recursos; no basta con afrontamiento individual."
        ),
        "intervencion_primaria": (
            "Dimensionar plantillas, regular jornada y reducir exposiciones emocionales/ambientales innecesarias."
        ),
        "intervencion_secundaria": (
            "Plan de alivio de picos de demanda y vigilancia de fatiga."
        ),
    },
    "Recompensas": {
        "instrumento": "intra",
        "dominio": "Recompensas",
        "definicion": (
            "Agrupa reconocimiento, compensación y sentido de pertenencia. Cierra el modelo esfuerzo-recompensa."
        ),
        "interpretacion_alto": (
            "Esfuerzo alto con recompensa baja es un patrón de alto riesgo cardiovascular y de rotación en la literatura del modelo de Siegrist."
        ),
        "intervencion_primaria": (
            "Equidad, reconocimiento sistemático y comunicación del valor del trabajo."
        ),
        "intervencion_secundaria": (
            "Revisión salarial y de beneficios en cargos con brecha percibida demostrable."
        ),
    },
}


def narrativa(nombre: str) -> Dict[str, str]:
    return NARRATIVAS.get(nombre) or {
        "instrumento": "intra",
        "dominio": "",
        "definicion": f"Dimensión normativa «{nombre}» de la Batería de Instrumentos para la Evaluación de Factores de Riesgo Psicosocial.",
        "interpretacion_alto": (
            "La concentración de trabajadores en riesgo alto o muy alto en esta dimensión "
            "debe incluirse en el Programa de Vigilancia Epidemiológica de factores psicosociales."
        ),
        "intervencion_primaria": "Priorizar esta dimensión en el plan de intervención anual del SG-SST.",
        "intervencion_secundaria": "Hacer seguimiento semestral del baremo y contrastar con indicadores de ausentismo y clima.",
    }


def interpolar_lectura(
    nombre: str,
    pct_critico: float,
    n_critico: int,
    n_eval: int,
    media: Optional[float],
) -> str:
    nav = narrativa(nombre)
    media_txt = f"{media:.1f}" if media is not None else "s.d."
    return (
        f"La dimensión «{nombre}» presenta {pct_critico:.1f}% de la muestra en riesgo alto o muy alto "
        f"(n={n_critico} de {n_eval}). Media del puntaje transformado: {media_txt}. "
        f"{nav['interpretacion_alto']}"
    )


def catalogo_para_siembra() -> list[Dict[str, Any]]:
    """Filas para catalogo_dimensiones (incluye dominios y síntoma de estrés)."""
    filas = []
    vistos = set()
    orden = 0
    for nombre in ORDEN_DOMINIOS + ORDEN_INTRA + ORDEN_EXTRA + ["Síntomas de estrés"]:
        if nombre in vistos:
            continue
        vistos.add(nombre)
        nav = narrativa(nombre)
        orden += 1
        filas.append(
            {
                "codigo": codigo_de(nombre, nav.get("instrumento", "intra")),
                "nombre": nombre,
                "instrumento": nav.get("instrumento", "intra"),
                "dominio": nav.get("dominio") or None,
                "definicion": nav.get("definicion") or "",
                "interpretacion_alto": nav.get("interpretacion_alto") or "",
                "intervencion_primaria": nav.get("intervencion_primaria") or "",
                "intervencion_secundaria": nav.get("intervencion_secundaria") or "",
                "orden": orden,
            }
        )
    totales = [
        ("intra", "Total Intralaboral", "Puntaje transformado global del cuestionario de factores de riesgo psicosocial intralaboral."),
        ("extra", "Total Extralaboral", "Puntaje transformado global del cuestionario de factores de riesgo psicosocial extralaboral."),
        ("estres", "Total Estrés", "Puntaje transformado global del cuestionario para la evaluación del estrés (3.ª versión)."),
        ("general", "Total General (Intra + Extra)", "Combinación de puntajes transformados intralaborales y extralaborales (Tabla 34)."),
    ]
    for inst, nombre, definicion in totales:
        orden += 1
        filas.append(
            {
                "codigo": CODIGOS_TOTAL[inst],
                "nombre": nombre,
                "instrumento": inst,
                "dominio": None,
                "definicion": definicion,
                "interpretacion_alto": (
                    "Un total en riesgo alto o muy alto indica que el conjunto del instrumento, "
                    "y no solo una dimensión aislada, requiere intervención prioritaria en el PVE."
                ),
                "intervencion_primaria": "Priorizar el instrumento en el plan anual de intervención psicosocial.",
                "intervencion_secundaria": "Reevaluar el total en la siguiente medición y contrastar con ausentismo y clima.",
                "orden": orden,
            }
        )
    return filas


def baremos_para_siembra() -> list[Tuple[str, str, Tuple[float, float, float, float]]]:
    """(dimension_codigo, forma, cortes) desde scoring.py."""
    from ..scoring import (
        BAREMOS_DIM_A,
        BAREMOS_DIM_B,
        BAREMOS_DOM_A,
        BAREMOS_DOM_B,
        BAREMOS_ESTRES_AUX,
        BAREMOS_ESTRES_JEFES,
        BAREMOS_EXTRA_DIM_A,
        BAREMOS_EXTRA_DIM_B,
        BAREMOS_EXTRA_TOTAL_AUX,
        BAREMOS_EXTRA_TOTAL_JEFES,
        BAREMOS_TOTAL_A,
        BAREMOS_TOTAL_B,
        BAREMOS_TOTAL_GENERAL_A,
        BAREMOS_TOTAL_GENERAL_B,
    )

    rows: list[Tuple[str, str, Tuple[float, float, float, float]]] = []
    for nombre, cortes in BAREMOS_DIM_A.items():
        rows.append((codigo_de(nombre, "intra"), "A", cortes))
    for nombre, cortes in BAREMOS_DIM_B.items():
        rows.append((codigo_de(nombre, "intra"), "B", cortes))
    for nombre, cortes in BAREMOS_DOM_A.items():
        rows.append((codigo_de(nombre, "intra"), "A", cortes))
    for nombre, cortes in BAREMOS_DOM_B.items():
        rows.append((codigo_de(nombre, "intra"), "B", cortes))
    for nombre, cortes in BAREMOS_EXTRA_DIM_A.items():
        rows.append((codigo_de(nombre, "extra"), "A", cortes))
    for nombre, cortes in BAREMOS_EXTRA_DIM_B.items():
        rows.append((codigo_de(nombre, "extra"), "B", cortes))
    rows.append((CODIGOS_TOTAL["intra"], "A", BAREMOS_TOTAL_A))
    rows.append((CODIGOS_TOTAL["intra"], "B", BAREMOS_TOTAL_B))
    rows.append((CODIGOS_TOTAL["extra"], "A", BAREMOS_EXTRA_TOTAL_JEFES))
    rows.append((CODIGOS_TOTAL["extra"], "B", BAREMOS_EXTRA_TOTAL_AUX))
    rows.append((CODIGOS_TOTAL["estres"], "A", BAREMOS_ESTRES_JEFES))
    rows.append((CODIGOS_TOTAL["estres"], "B", BAREMOS_ESTRES_AUX))
    rows.append((CODIGOS_TOTAL["general"], "A", BAREMOS_TOTAL_GENERAL_A))
    rows.append((CODIGOS_TOTAL["general"], "B", BAREMOS_TOTAL_GENERAL_B))
    return rows
