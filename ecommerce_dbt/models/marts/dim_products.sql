with products as (
    select * from {{ ref('stg_products') }}
),

order_items as (
    select
        product_id,
        count(*)        as times_ordered,
        sum(price)      as total_revenue
    from {{ ref('stg_order_items') }}
    group by product_id
),

final as (
    select
        p.product_id,
        p.category_name,
        p.weight_g,
        i.times_ordered,
        i.total_revenue
    from products p
    left join order_items i on p.product_id = i.product_id
)

select * from final