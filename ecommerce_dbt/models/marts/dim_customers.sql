with customers as (
    select * from {{ ref('stg_customers') }}
),

orders as (
    select
        customer_id,
        count(*)                    as total_orders,
        sum(total_payment)          as total_spent,
        min(ordered_at)             as first_order_at,
        max(ordered_at)             as last_order_at,
        avg(review_score)           as avg_review_score
    from {{ ref('fct_orders') }}
    group by customer_id
),

final as (
    select
        c.customer_id,
        c.customer_unique_id,
        c.city,
        c.state,
        o.total_orders,
        o.total_spent,
        o.first_order_at,
        o.last_order_at,
        o.avg_review_score
    from customers c
    left join orders o on c.customer_id = o.customer_id
)

select * from final