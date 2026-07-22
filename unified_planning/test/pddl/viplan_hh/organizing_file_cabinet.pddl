(define (problem organizing_file_cabinet_0)
    (:domain igibson)

    (:objects
        marker_1 - movable
        table_1 - object
        cabinet_1 - container
        document_1 document_2 document_3 document_4 - movable
        folder_1 folder_2 - movable
    )

    (:init
    )

    (:goal
        (and
            (ontop marker_1 table_1)
            (inside document_1 cabinet_1)
            (inside document_3 cabinet_1)
        )
    )
)
