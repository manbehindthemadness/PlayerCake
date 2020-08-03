PlayerCake: Firmware application designed to provide rapid kinematic instructions to multi-legged robitoc platforms.
Kevin Eales 2020


Vocabulary:

Applications:
    playercake.writer: This is the prerendering application that produces the script files used by stage.
    playercake.stage: This is the client app that handles the real time processing on the down-stream mobile platform.
    playercake.director: This is the central control app, it is designed to manage one or more down-stream mobile platforms running stage.
    playercake.audience: This is the visual interface application designed to render the result sets provided by director.
    playercake.warehouse: This is where resources (code and things) that are shared across the above applications is stored.

Terms:
    Rehersals: Raw movement instructions that will be pre-processed into a Script.
    Script: A pre-rendered result of a Rehersal collection of movement instructions. These are used as the foundation for kinamatic operations.
    lines: A Line is a single interation if specific instructions within a Script.
    Scenes: Scenes are sequential collections of one or more scripts resulting in a procedure (like taking a step).
    Plays: Collections of one or more scenes specifying an end-goal.
    Intermissions: Once a Play is complete we will take an Intermission and report back to Director.
    Actor: Any extremity that relates to movement in the physical world (such as a servo or stepper).
    Improvisers: These are real-time data factors that alter the behavior of Scripts (gyro, accelerometer...etc).
    Props: Sensors providing information about the physical world (echolocation, laser, IR...etc)
    Cues: Any conditional interrupt that results in an action being taken (there is a wall in front of me...).
    Critics: These conditionally discourage certain queues depending on what kind of Scene we are using.
    Performance: This is a rating attached to Scripts, Scenes, plays and Directors respectively. The value signifies effectiveness.
    Heckles: These are direct commands sent from Audience that effect the behavior of one or more Stages.