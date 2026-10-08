// Hotel PMS - Global JS helpers
frappe.provide('hotel_pms');

hotel_pms.get_room_status_color = function(status) {
    const colors = {
        'Available': 'green',
        'Reserved': 'blue',
        'Occupied': 'red',
        'Cleaning': 'orange',
        'Maintenance': 'grey',
        'Blocked': 'darkgrey',
        'Out of Service': 'black'
    };
    return colors[status] || 'grey';
};

hotel_pms.format_currency = function(amount) {
    return frappe.format(amount, {fieldtype: 'Currency'});
};
