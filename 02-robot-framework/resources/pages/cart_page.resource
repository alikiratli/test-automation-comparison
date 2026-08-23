*** Settings ***
Documentation       Sepet sayfasi keyword'leri.

Resource            ../common.resource


*** Variables ***
${CART_LIST}                css:[data-test='cart-list']
${CART_ITEM}                css:.cart_item
${CART_ITEM_NAME}           css:[data-test='inventory-item-name']
${CART_ITEM_PRICE}          css:[data-test='inventory-item-price']
${CART_ITEM_QUANTITY}       css:[data-test='item-quantity']
${CHECKOUT_BUTTON}          css:[data-test='checkout']
${CONTINUE_SHOPPING}        css:[data-test='continue-shopping']


*** Keywords ***
Cart Page Should Be Open
    Wait Until Location Contains    cart.html    ${DEFAULT_TIMEOUT}
    Wait Until Element Is Visible    ${CART_LIST}    ${DEFAULT_TIMEOUT}

Go To Cart Page
    Go To    ${CART_URL}
    Wait For Page To Be Ready
    Cart Page Should Be Open

Get Cart Item Count
    ${elements} =    Get WebElements    ${CART_ITEM}
    ${count} =    Get Length    ${elements}
    RETURN    ${count}

Get Cart Item Names
    ${count} =    Get Cart Item Count
    IF    ${count} == 0
        ${empty} =    Create List
        RETURN    ${empty}
    END
    ${names} =    Get Texts From Elements    ${CART_ITEM_NAME}
    RETURN    ${names}

Get Cart Item Prices
    ${texts} =    Get Texts From Elements    ${CART_ITEM_PRICE}
    ${prices} =    Parse Prices    ${texts}
    RETURN    ${prices}

Get Cart Subtotal
    [Documentation]    Sepet satirlarindan ara toplami HESAPLAR.
    ...    Bu deger, checkout ozetindeki tutarla karsilastirilarak
    ...    uygulamanin hesap dogrulugu test edilir.
    ${prices} =    Get Cart Item Prices
    ${subtotal} =    Evaluate    round(sum(${prices}), 2)
    RETURN    ${subtotal}

Cart Should Be Empty
    ${count} =    Get Cart Item Count
    Should Be Equal As Integers    ${count}    0    msg=Sepet bos degil

Cart Should Contain
    [Arguments]    ${product_name}
    ${names} =    Get Cart Item Names
    Should Contain    ${names}    ${product_name}
    ...    msg=Urun sepette bulunamadi: ${product_name}

Cart Should Not Contain
    [Arguments]    ${product_name}
    ${names} =    Get Cart Item Names
    Should Not Contain    ${names}    ${product_name}
    ...    msg=Urun hala sepette: ${product_name}

Cart Should Contain Exactly
    [Arguments]    @{expected_products}
    ${names} =    Get Cart Item Names
    Verify Sets Are Equal    ${names}    ${expected_products}    label=Sepet icerigi

Remove Item From Cart
    [Documentation]    Urunu sepetten siler ve satir sayisinin AZALMASINI bekler.
    [Arguments]    ${product_name}
    ${before} =    Get Cart Item Count
    ${locator} =    Remove From Cart Locator    ${product_name}
    ${expected} =    Evaluate    ${before} - 1
    Click Element Until    ${locator}
    ...    Wait Until Keyword Succeeds    3s    200ms    Cart Item Count Should Be    ${expected}

Cart Item Count Should Be
    [Arguments]    ${expected}
    ${actual} =    Get Cart Item Count
    Should Be Equal As Integers    ${actual}    ${expected}

All Cart Quantities Should Be One
    ${quantities} =    Get Texts From Elements    ${CART_ITEM_QUANTITY}
    FOR    ${quantity}    IN    @{quantities}
        Should Be Equal As Integers    ${quantity}    1
        ...    msg=Beklenmeyen adet: ${quantity}
    END

Cart Prices Should Match Reference Data
    ${names} =    Get Cart Item Names
    ${prices} =    Get Cart Item Prices
    FOR    ${index}    ${name}    IN ENUMERATE    @{names}
        ${actual} =    Get From List    ${prices}    ${index}
        ${expected} =    Get From Dictionary    ${PRODUCTS}    ${name}
        Run Keyword And Continue On Failure
        ...    Should Be Equal As Numbers    ${actual}    ${expected}
        ...    msg=Sepetteki ${name} fiyati hatali
    END

Proceed To Checkout
    Click And Wait For Location    ${CHECKOUT_BUTTON}    checkout-step-one.html
    Wait Until Element Is Visible    css:[data-test='firstName']    ${DEFAULT_TIMEOUT}

Continue Shopping
    Click And Wait For Location    ${CONTINUE_SHOPPING}    inventory.html
