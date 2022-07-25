(define (problem problem_name) (:domain domain_name)
(:objects
    r1 r2 r3 - robot
    f1 f2 f3 - fastener
)

(:init
    (fastener_selected f1)
    (robot_uninitialized r1)
    (robot_free r1)
)

(:goal (and
    (goal_reached r1)
))

)
