(define (domain logistics-objfluents)
    (:requirements :typing :object-fluents)
    (:types
        location - object
        vehicle - object
        package - object
    )

    (:predicates
        (connected ?from - location ?to - location)
    )

    (:functions
        (vehicle_at ?v - vehicle) - location
        (package_at ?p - package) - location
        (cargo ?v - vehicle) - package
    )

    (:action drive
        :parameters (?v - vehicle ?from - location ?to - location)
        :precondition (and
            (= (vehicle_at ?v) ?from)
            (connected ?from ?to)
        )
        :effect (assign (vehicle_at ?v) ?to)
    )

    (:action load
        :parameters (?v - vehicle ?p - package ?loc - location)
        :precondition (and
            (= (vehicle_at ?v) ?loc)
            (= (package_at ?p) ?loc)
        )
        :effect (assign (cargo ?v) ?p)
    )
)
