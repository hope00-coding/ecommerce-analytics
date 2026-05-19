with source as (
    select * from {{ source('raw', 'raw_reviews') }}
),
renamed as (
    select
        review_id,
        order_id,
        review_score,
        cast(review_creation_date as timestamp)  as created_at,
        cast(review_answer_timestamp as timestamp) as answered_at
    from source
)
select * from renamed