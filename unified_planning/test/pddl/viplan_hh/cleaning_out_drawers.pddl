(define (problem cleaning_out_drawers_0)
    (:domain igibson)

    (:objects
     	bowl_1 - movable
    	cabinet_1 - container
    	sink_1 - object
    )
    
    (:init 
        (inside bowl_1 cabinet_1) 
        (not (open cabinet_1))
    )
    
    (:goal 
        (and 
            (ontop bowl_1 sink_1) 
        )
    )
)