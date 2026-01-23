from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Observations(_message.Message):
    __slots__ = ("agents",)
    AGENTS_FIELD_NUMBER: _ClassVar[int]
    agents: _containers.RepeatedCompositeFieldContainer[AgentObservation]
    def __init__(self, agents: _Optional[_Iterable[_Union[AgentObservation, _Mapping]]] = ...) -> None: ...

class Step(_message.Message):
    __slots__ = ("controls", "stepCount", "timeScale")
    CONTROLS_FIELD_NUMBER: _ClassVar[int]
    STEPCOUNT_FIELD_NUMBER: _ClassVar[int]
    TIMESCALE_FIELD_NUMBER: _ClassVar[int]
    controls: _containers.RepeatedCompositeFieldContainer[AgentControls]
    stepCount: int
    timeScale: float
    def __init__(self, controls: _Optional[_Iterable[_Union[AgentControls, _Mapping]]] = ..., stepCount: _Optional[int] = ..., timeScale: _Optional[float] = ...) -> None: ...

class TakeScreenshot(_message.Message):
    __slots__ = ("position", "orientationEuler")
    POSITION_FIELD_NUMBER: _ClassVar[int]
    ORIENTATIONEULER_FIELD_NUMBER: _ClassVar[int]
    position: Vector3
    orientationEuler: Vector3
    def __init__(self, position: _Optional[_Union[Vector3, _Mapping]] = ..., orientationEuler: _Optional[_Union[Vector3, _Mapping]] = ...) -> None: ...

class Reset(_message.Message):
    __slots__ = ("envsToReset", "reloadScene", "cameraPosition")
    ENVSTORESET_FIELD_NUMBER: _ClassVar[int]
    RELOADSCENE_FIELD_NUMBER: _ClassVar[int]
    CAMERAPOSITION_FIELD_NUMBER: _ClassVar[int]
    envsToReset: _containers.RepeatedCompositeFieldContainer[ResetParameters]
    reloadScene: bool
    cameraPosition: Transform
    def __init__(self, envsToReset: _Optional[_Iterable[_Union[ResetParameters, _Mapping]]] = ..., reloadScene: bool = ..., cameraPosition: _Optional[_Union[Transform, _Mapping]] = ...) -> None: ...

class ResetParameters(_message.Message):
    __slots__ = ("index", "envCubeBowl", "envTableware", "envTrashPicking", "envSpheres")
    INDEX_FIELD_NUMBER: _ClassVar[int]
    ENVCUBEBOWL_FIELD_NUMBER: _ClassVar[int]
    ENVTABLEWARE_FIELD_NUMBER: _ClassVar[int]
    ENVTRASHPICKING_FIELD_NUMBER: _ClassVar[int]
    ENVSPHERES_FIELD_NUMBER: _ClassVar[int]
    index: int
    envCubeBowl: EnvCubeBowlParameters
    envTableware: EnvTablewareParameters
    envTrashPicking: EnvTrashPickingParameters
    envSpheres: EnvSpheresParameters
    def __init__(self, index: _Optional[int] = ..., envCubeBowl: _Optional[_Union[EnvCubeBowlParameters, _Mapping]] = ..., envTableware: _Optional[_Union[EnvTablewareParameters, _Mapping]] = ..., envTrashPicking: _Optional[_Union[EnvTrashPickingParameters, _Mapping]] = ..., envSpheres: _Optional[_Union[EnvSpheresParameters, _Mapping]] = ...) -> None: ...

class EnvSpheresParameters(_message.Message):
    __slots__ = ("sphereRed", "sphereGreen", "sphereYellow", "goal", "agentPosition")
    SPHERERED_FIELD_NUMBER: _ClassVar[int]
    SPHEREGREEN_FIELD_NUMBER: _ClassVar[int]
    SPHEREYELLOW_FIELD_NUMBER: _ClassVar[int]
    GOAL_FIELD_NUMBER: _ClassVar[int]
    AGENTPOSITION_FIELD_NUMBER: _ClassVar[int]
    sphereRed: Transform
    sphereGreen: Transform
    sphereYellow: Transform
    goal: Transform
    agentPosition: Transform
    def __init__(self, sphereRed: _Optional[_Union[Transform, _Mapping]] = ..., sphereGreen: _Optional[_Union[Transform, _Mapping]] = ..., sphereYellow: _Optional[_Union[Transform, _Mapping]] = ..., goal: _Optional[_Union[Transform, _Mapping]] = ..., agentPosition: _Optional[_Union[Transform, _Mapping]] = ...) -> None: ...

class EnvCubeBowlParameters(_message.Message):
    __slots__ = ("bowl", "cubeRed", "cubeBlue", "cubeGreen", "cubeYellow", "agentPosition")
    BOWL_FIELD_NUMBER: _ClassVar[int]
    CUBERED_FIELD_NUMBER: _ClassVar[int]
    CUBEBLUE_FIELD_NUMBER: _ClassVar[int]
    CUBEGREEN_FIELD_NUMBER: _ClassVar[int]
    CUBEYELLOW_FIELD_NUMBER: _ClassVar[int]
    AGENTPOSITION_FIELD_NUMBER: _ClassVar[int]
    bowl: Transform
    cubeRed: Transform
    cubeBlue: Transform
    cubeGreen: Transform
    cubeYellow: Transform
    agentPosition: Transform
    def __init__(self, bowl: _Optional[_Union[Transform, _Mapping]] = ..., cubeRed: _Optional[_Union[Transform, _Mapping]] = ..., cubeBlue: _Optional[_Union[Transform, _Mapping]] = ..., cubeGreen: _Optional[_Union[Transform, _Mapping]] = ..., cubeYellow: _Optional[_Union[Transform, _Mapping]] = ..., agentPosition: _Optional[_Union[Transform, _Mapping]] = ...) -> None: ...

class EnvTablewareParameters(_message.Message):
    __slots__ = ("plate", "knife", "spoon", "fork", "glass", "agentPosition")
    PLATE_FIELD_NUMBER: _ClassVar[int]
    KNIFE_FIELD_NUMBER: _ClassVar[int]
    SPOON_FIELD_NUMBER: _ClassVar[int]
    FORK_FIELD_NUMBER: _ClassVar[int]
    GLASS_FIELD_NUMBER: _ClassVar[int]
    AGENTPOSITION_FIELD_NUMBER: _ClassVar[int]
    plate: Transform
    knife: Transform
    spoon: Transform
    fork: Transform
    glass: Transform
    agentPosition: Transform
    def __init__(self, plate: _Optional[_Union[Transform, _Mapping]] = ..., knife: _Optional[_Union[Transform, _Mapping]] = ..., spoon: _Optional[_Union[Transform, _Mapping]] = ..., fork: _Optional[_Union[Transform, _Mapping]] = ..., glass: _Optional[_Union[Transform, _Mapping]] = ..., agentPosition: _Optional[_Union[Transform, _Mapping]] = ...) -> None: ...

class EnvTrashPickingParameters(_message.Message):
    __slots__ = ("agentPosition", "binGreen", "binYellow", "binBlue", "trashPaper", "trashFood", "trashMetal")
    AGENTPOSITION_FIELD_NUMBER: _ClassVar[int]
    BINGREEN_FIELD_NUMBER: _ClassVar[int]
    BINYELLOW_FIELD_NUMBER: _ClassVar[int]
    BINBLUE_FIELD_NUMBER: _ClassVar[int]
    TRASHPAPER_FIELD_NUMBER: _ClassVar[int]
    TRASHFOOD_FIELD_NUMBER: _ClassVar[int]
    TRASHMETAL_FIELD_NUMBER: _ClassVar[int]
    agentPosition: Transform
    binGreen: Transform
    binYellow: Transform
    binBlue: Transform
    trashPaper: Transform
    trashFood: Transform
    trashMetal: Transform
    def __init__(self, agentPosition: _Optional[_Union[Transform, _Mapping]] = ..., binGreen: _Optional[_Union[Transform, _Mapping]] = ..., binYellow: _Optional[_Union[Transform, _Mapping]] = ..., binBlue: _Optional[_Union[Transform, _Mapping]] = ..., trashPaper: _Optional[_Union[Transform, _Mapping]] = ..., trashFood: _Optional[_Union[Transform, _Mapping]] = ..., trashMetal: _Optional[_Union[Transform, _Mapping]] = ...) -> None: ...

class Configure(_message.Message):
    __slots__ = ("envsToConfigure",)
    ENVSTOCONFIGURE_FIELD_NUMBER: _ClassVar[int]
    envsToConfigure: _containers.RepeatedCompositeFieldContainer[ConfigureParameters]
    def __init__(self, envsToConfigure: _Optional[_Iterable[_Union[ConfigureParameters, _Mapping]]] = ...) -> None: ...

class AgentObservation(_message.Message):
    __slots__ = ("index", "transformsByNameArmFrame", "transformsByNameEnvFrame", "currentJointAnglesDeg", "gripSuccessful", "isBetweenGripper", "betweenGripper", "linkTransformsArm", "linkTransformsArmRelative")
    class TransformsByNameArmFrameEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: Transform
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[Transform, _Mapping]] = ...) -> None: ...
    class TransformsByNameEnvFrameEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: Transform
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[Transform, _Mapping]] = ...) -> None: ...
    INDEX_FIELD_NUMBER: _ClassVar[int]
    TRANSFORMSBYNAMEARMFRAME_FIELD_NUMBER: _ClassVar[int]
    TRANSFORMSBYNAMEENVFRAME_FIELD_NUMBER: _ClassVar[int]
    CURRENTJOINTANGLESDEG_FIELD_NUMBER: _ClassVar[int]
    GRIPSUCCESSFUL_FIELD_NUMBER: _ClassVar[int]
    ISBETWEENGRIPPER_FIELD_NUMBER: _ClassVar[int]
    BETWEENGRIPPER_FIELD_NUMBER: _ClassVar[int]
    LINKTRANSFORMSARM_FIELD_NUMBER: _ClassVar[int]
    LINKTRANSFORMSARMRELATIVE_FIELD_NUMBER: _ClassVar[int]
    index: int
    transformsByNameArmFrame: _containers.MessageMap[str, Transform]
    transformsByNameEnvFrame: _containers.MessageMap[str, Transform]
    currentJointAnglesDeg: _containers.RepeatedScalarFieldContainer[float]
    gripSuccessful: bool
    isBetweenGripper: bool
    betweenGripper: str
    linkTransformsArm: _containers.RepeatedCompositeFieldContainer[Transform]
    linkTransformsArmRelative: _containers.RepeatedCompositeFieldContainer[Transform]
    def __init__(self, index: _Optional[int] = ..., transformsByNameArmFrame: _Optional[_Mapping[str, Transform]] = ..., transformsByNameEnvFrame: _Optional[_Mapping[str, Transform]] = ..., currentJointAnglesDeg: _Optional[_Iterable[float]] = ..., gripSuccessful: bool = ..., isBetweenGripper: bool = ..., betweenGripper: _Optional[str] = ..., linkTransformsArm: _Optional[_Iterable[_Union[Transform, _Mapping]]] = ..., linkTransformsArmRelative: _Optional[_Iterable[_Union[Transform, _Mapping]]] = ...) -> None: ...

class AgentControls(_message.Message):
    __slots__ = ("index", "jointTargetsDeg", "activateGrip", "targetBasePose", "baseImmobile")
    INDEX_FIELD_NUMBER: _ClassVar[int]
    JOINTTARGETSDEG_FIELD_NUMBER: _ClassVar[int]
    ACTIVATEGRIP_FIELD_NUMBER: _ClassVar[int]
    TARGETBASEPOSE_FIELD_NUMBER: _ClassVar[int]
    BASEIMMOBILE_FIELD_NUMBER: _ClassVar[int]
    index: int
    jointTargetsDeg: _containers.RepeatedScalarFieldContainer[float]
    activateGrip: bool
    targetBasePose: Transform
    baseImmobile: bool
    def __init__(self, index: _Optional[int] = ..., jointTargetsDeg: _Optional[_Iterable[float]] = ..., activateGrip: bool = ..., targetBasePose: _Optional[_Union[Transform, _Mapping]] = ..., baseImmobile: bool = ...) -> None: ...

class ConfigureParameters(_message.Message):
    __slots__ = ("index", "linkParameters", "wheelParameters")
    INDEX_FIELD_NUMBER: _ClassVar[int]
    LINKPARAMETERS_FIELD_NUMBER: _ClassVar[int]
    WHEELPARAMETERS_FIELD_NUMBER: _ClassVar[int]
    index: int
    linkParameters: _containers.RepeatedCompositeFieldContainer[LinkParameters]
    wheelParameters: WheelParameters
    def __init__(self, index: _Optional[int] = ..., linkParameters: _Optional[_Iterable[_Union[LinkParameters, _Mapping]]] = ..., wheelParameters: _Optional[_Union[WheelParameters, _Mapping]] = ...) -> None: ...

class LinkParameters(_message.Message):
    __slots__ = ("linkIndex", "stiffness", "damping", "forceLimit")
    LINKINDEX_FIELD_NUMBER: _ClassVar[int]
    STIFFNESS_FIELD_NUMBER: _ClassVar[int]
    DAMPING_FIELD_NUMBER: _ClassVar[int]
    FORCELIMIT_FIELD_NUMBER: _ClassVar[int]
    linkIndex: int
    stiffness: float
    damping: float
    forceLimit: float
    def __init__(self, linkIndex: _Optional[int] = ..., stiffness: _Optional[float] = ..., damping: _Optional[float] = ..., forceLimit: _Optional[float] = ...) -> None: ...

class WheelParameters(_message.Message):
    __slots__ = ("torque", "velocityPID", "yawPID")
    TORQUE_FIELD_NUMBER: _ClassVar[int]
    VELOCITYPID_FIELD_NUMBER: _ClassVar[int]
    YAWPID_FIELD_NUMBER: _ClassVar[int]
    torque: float
    velocityPID: PID
    yawPID: PID
    def __init__(self, torque: _Optional[float] = ..., velocityPID: _Optional[_Union[PID, _Mapping]] = ..., yawPID: _Optional[_Union[PID, _Mapping]] = ...) -> None: ...

class Transform(_message.Message):
    __slots__ = ("position", "euler", "orientation")
    POSITION_FIELD_NUMBER: _ClassVar[int]
    EULER_FIELD_NUMBER: _ClassVar[int]
    ORIENTATION_FIELD_NUMBER: _ClassVar[int]
    position: Vector3
    euler: Vector3
    orientation: Quaternion
    def __init__(self, position: _Optional[_Union[Vector3, _Mapping]] = ..., euler: _Optional[_Union[Vector3, _Mapping]] = ..., orientation: _Optional[_Union[Quaternion, _Mapping]] = ...) -> None: ...

class PID(_message.Message):
    __slots__ = ("kp", "kd", "ki")
    KP_FIELD_NUMBER: _ClassVar[int]
    KD_FIELD_NUMBER: _ClassVar[int]
    KI_FIELD_NUMBER: _ClassVar[int]
    kp: float
    kd: float
    ki: float
    def __init__(self, kp: _Optional[float] = ..., kd: _Optional[float] = ..., ki: _Optional[float] = ...) -> None: ...

class Vector3(_message.Message):
    __slots__ = ("x", "y", "z")
    X_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    Z_FIELD_NUMBER: _ClassVar[int]
    x: float
    y: float
    z: float
    def __init__(self, x: _Optional[float] = ..., y: _Optional[float] = ..., z: _Optional[float] = ...) -> None: ...

class Quaternion(_message.Message):
    __slots__ = ("x", "y", "z", "w")
    X_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    Z_FIELD_NUMBER: _ClassVar[int]
    W_FIELD_NUMBER: _ClassVar[int]
    x: float
    y: float
    z: float
    w: float
    def __init__(self, x: _Optional[float] = ..., y: _Optional[float] = ..., z: _Optional[float] = ..., w: _Optional[float] = ...) -> None: ...
