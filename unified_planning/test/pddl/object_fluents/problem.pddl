(define (problem deliver-pkg)
    (:domain logistics-objfluents)
    (:objects
        loc1 loc2 loc3 - location
        truck1 - vehicle
        pkg1 - package
    )

    (:init
        (connected loc1 loc2)
        (connected loc2 loc3)
        (= (vehicle_at truck1) loc1)
        (= (package_at pkg1) loc2)
    )

    (:goal
        (= (package_at pkg1) loc3)
    )
)
