(define (problem putting_away_toys_0)
    (:domain igibson)

    (:objects
        plaything_1 plaything_2 plaything_3 plaything_4 - movable
        carton_1 - container
        table_1 - object
    )
    
    (:init 
        (open carton_1)
    )
    
    (:goal 
        (and 
            (inside plaything_4 carton_1)
            (inside plaything_2 carton_1)
        )
    )
)