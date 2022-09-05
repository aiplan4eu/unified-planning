; PDDL forall effect with durative actions

(define (domain domain_name)

(:requirements :strips :fluents :durative-actions :timed-initial-literals :typing :conditional-effects :negative-preconditions :duration-inequalities :equality)

(:types robot fastener
)

(:predicates
    (robot_uninitialized ?r - robot)
    (robot_free ?r - robot)
    (fastener_selected ?f - fastener)
    (goal_reached ?r - robot)
)


(:functions
    (robot_on_fastener_number_in_sequence)
)

(:durative-action init
    :parameters (?r - robot)
    :duration ( = ?duration 1)
    :condition (and
        (at start (robot_uninitialized ?r))
        (at start (robot_free ?r))
        (at end (forall (?f - fastener)
            (fastener_selected ?f))
        )
    )
    :effect (and
        (at start(not(robot_free ?r)))
        (at end (assign (robot_on_fastener_number_in_sequence) 1))
        (at end (not(robot_uninitialized ?r)))
        (at end (robot_free ?r))
        (forall (?f - fastener)
            (at end (not (fastener_selected ?f)))
        )
        (at end (goal_reached ?r))
    )
)

)
