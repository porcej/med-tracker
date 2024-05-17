// Main / parent / top level Editor
let encounterTable;
const encounterEditor = new DataTable.Editor({
    ajax: './api/encounters'.concat(window.current_aid_station_path),
    table: '#encounters-table',
    idSrc: 'id',
    fields: [
         {
            label: 'Bib Number',
            name: 'bib'
        },
        {
            label: 'First Name',
            name: 'first_name'
        },
        {
            label: 'Last Name',
            name: 'last_name'
        },
        {
            label: 'Age',
            name: 'age'
        },
        {
            label: 'Sex',
            name: 'sex',
            type: 'select',
            options: [
                { label: '', value: '' },
                { label: 'Male', value: 'M' },
                { label: 'Female', value: 'F' },
                // { label: 'Other', value: 'Other' },
            ]
        },
        {
            label: 'Race Partipant',
            name: 'runner_type',
            type: 'select',
            options: [
                { label: 'Yes', value: 'yes' },
                { label: 'No', value: ''}
                // { label: 'Civilian', value: 'Civilian'},
                // { label: 'Volunteer', value: 'Volunteer'},
                // { label: 'Military', value: 'Military'}
            ]
        },
        {
            label: "Time into Aid Station",
            name: "time_in",
            type: 'datetime',
            format: 'HH:mm',
            fieldInfo: '24 hour clock (HH:mm)'
        },
        {
            label: 'Time out of Aid Station',
            name: 'time_out',
            type: 'datetime',
            format: 'HH:mm',
            fieldInfo: '24 hour clock (HH:mm)'
        },
        {
            // label: 'Primary Complaint',
            label: 'Presents',
            name: 'presentation',
            type: 'select',
            options: [
                { label: '', value: ''  },
                { label: 'AX        Allergic Rxn', value: 'Allergic Rxn' },
                { label: 'IB         Insect/ Bee', value: 'Insect/ Bee' },
                { label: 'Br   Breathing Problem', value: 'Breathing Problem' },
                { label: 'As              Asthma', value: 'Asthma' },
                { label: 'Fi         Feeling Ill', value: 'Feeling Ill' },
                { label: 'VI       Vision Issues', value: 'Vision Issues' },
                { label: 'CD    Chest Discomfort', value: 'Chest Discomfort' },
                { label: 'Dh         Dysrhythmia', value: 'Dysrhythmia' },
                { label: 'B              Blister', value: 'Blister' },
                { label: 'A             Abrasion', value: 'Abrasion' },
                { label: 'Oy        Onychoptosis', value: 'Onychoptosis' },
                { label: 'W                Wound', value: 'Wound' },
                { label: 'S        Sprain/Strain', value: 'Sprain/Strain' },
                { label: 'C            Contusion', value: 'Contusion' },
                { label: 'T           Tendonitis', value: 'Tendonitis' },
                { label: 'F             Fracture', value: 'Fracture' },
                { label: 'Dz           Dizziness', value: 'Dizziness' },
                { label: 'NV    Nausea/ Vomiting', value: 'Nausea/ Vomiting' },
                { label: 'FW   Fatigue/ Weakness', value: 'Fatigue/ Weakness' },
                { label: 'MC           MM Cramps', value: 'MM Cramps' },
                { label: 'D          Dehydration', value: 'Dehydration' },
                { label: 'EC Exertional Collapse', value: 'Exertional Collapse' },
                { label: 'Ha            Headache', value: 'Headache' },
                { label: 'Dr            Diarrhea', value: 'Diarrhea' },
                { label: 'aMS        Alterned MS', value: 'Alterned MS' },
                { label: 'HE     Heat Exhaustion', value: 'Heat Exhaustion' },
                { label: 'HS         Heat Stroke', value: 'Heat Stroke' },
                { label: 'HN        Hyponatremia', value: 'Hyponatremia' },
                { label: 'LS        Hypoglycemia', value: 'Hypoglycemia' },
                { label: 'EE     Extremity Edema', value: 'Extremity Edema' },
                { label: 'Nb            Numbness', value: 'Numbness' },
                { label: 'LT.        Hypothermia', value: 'Hypothermia' },
                { label: 'Other - Specify in notes', value: 'Other' }
            ]
        },
        {
            label: 'Vitals',
            name: 'vitals',
            fieldInfo: 'List of Vital Signs, by time, please use [TIME TEMP RESP PULSE BP Meds, Fluids, Rx',
            type: 'textarea'
        },
        {
            label: 'IV Provided',
            name: "iv",
            type: 'select',
            options: [
                { label: 'None', value: ''  },
                { label: 'Right Arm', value: 'IV - Right Arm' },
                { label: 'Left Arm', value: 'IV - Left Arm' },
                { label: 'Other - Specify in notes', value: 'IV - Other' }
            ]
        },
        {
            label: 'Na+',
            name: 'na',
            fieldInfo: 'BMP - Sodium'
        },
        {
            label: 'K+',
            name: 'kplus',
            fieldInfo: 'BMP - Potassium'
        },
        {
            label: 'Cl-',
            name: 'cl',
            fieldInfo: 'BMP - Chlorine'
        },
        {
            label: 'tCO2',
            name: 'tco',
            fieldInfo: 'BMP - Bicarbonate'
        },
        {
            label: 'BUN',
            name: 'bun',
            fieldInfo: 'BMP - Blood Urea Nitrogen'
        },
        {
            label: 'Cr',
            name: 'cr',
            fieldInfo: 'BMP - Creatinine'
        },
                {
            label: 'Glu',
            name: 'glu',
            fieldInfo: 'BMP - Blood Glucose'
        },
        {
            label: 'Treatments',
            name: 'treatments',
            type: "textarea",
            fieldInfo: 'List treatment(s) provided, including use of ice, stretches, wound care, and physical therapy along with any other pertinent information.'
        },
        {
            label: 'Disposition',
            name: 'disposition',
            type: 'select',
            options: [
                { label: '', value: ''  },

                // Marine Corps Marathon Encounter
                // { label: 'Transport to Georgetown', value: 'Transport to Georgetown' },
                // { label: 'Transport to George Washington', value: 'Transport to George Washington' },
                // { label: 'Transport to Howard', value: 'Transport to Howard' },
                // { label: 'Transport to Washington Hosp Ctr', value: 'Transport to Washington Hosp Ctr' },
                // { label: 'Transport to INOVA Fairfax', value: 'Transport to INOVA Fairfax' },
                // { label: 'Transport to INOVA Alexandria', value: 'Transport to INOVA Alexandria' },
                // { label: 'Transport to VA Hosp Ctr', value: 'Transport to VA Hosp Ctr' },

                // Run with the Maries Medical Encounter
                { label: 'Transport to Mary Washington', value: 'Transport to Mary Washington' },
                { label: 'Transport to Sentara NOVA', value: 'Transport to Sentara NOVA' },
                { label: 'Transport to Stafford', value: 'Transport to Stafford' },
                { label: 'Transport to Ft Belvoir', value: 'Transport to Ft Belvoir' },
                { label: 'Transport to Naval Clinic Quantico', value: 'Transport to Naval Clinic Quantico' },
                { label: 'Transport to INOVA Alexandria', value: 'Transport to INOVA Alexandria' },
                { label: 'Transport to Spotsylvania Regional', value: 'Transport to Spotsylvania Regional' },

                // Common Dispositions
                { label: 'Transport to Other - Specify in notes', value: 'Transport to Other' },
                { label: 'Release to Resume Race', value: 'Release to Resume Race' },
                { label: 'Released Awaiting Bus', value: 'Released Awaiting Bus' },
                { label: 'Released Finished Race', value: 'Released Finished Race' },
                { label: 'Released Left Course', value: 'Released Left Course' },
                { label: 'Refused Trasnport', value: 'Refused Trasnport' },
                { label: 'Left Against Medical Advice', value: 'Left Against Medical Advice' },
                { label: 'Other Disposition - Specify in notes', value: 'Other Disposition' }
            ]
        },
        {
            label: 'Notes',
            name: 'notes',
            type: "textarea",
        },
        { 
            label: 'Aid Station',
            name: 'aid_station',
            type: 'select', 
            options: window.current_aid_station_options
        }        
    ]
});
 
// Encounters DataTable shown in the page
encounterTable = new DataTable('#encounters-table', {
    idSrc: 'id',
    ajax: './api/encounters'.concat(window.current_aid_station_path),
    columns: [
        { data: 'bib' },
        { data: 'first_name' },
        { data: 'last_name' },
        { data: 'time_in', },
        { data: 'time_out', },
        { data: 'presentation', },
        { data: 'disposition' },
        { data: 'aid_station' }
    ],
    layout: {
        topStart: {
            buttons: [
                { extend: 'create', editor: encounterEditor },
                { extend: 'edit', editor: encounterEditor },
                { extend: 'remove', editor: encounterEditor }
            ]
        }
    },
    select: {
        style: 'single'
    }
});


// Encounters DataTable shown in the page
let participantsTable = new DataTable('#participants-table', {
    idSrc: 'id',
    ajax: './api/participants/',
    columns: [
        { data: 'bib' },
        { data: 'first_name' },
        { data: 'last_name' },
        { data: 'age', searchable: false, targets: 0 },
        { data: 'sex', },
    ],
    select: {
        style: 'single'
    }
});

$(document).ready(function () {   
    // let table = $('#participants-table').DataTable();
    $('#participants-table tbody').on('click', 'tr', function () {
        const row = participantsTable.row(this).data();
        encounterEditor
            .create()
            .title(`New Encounter with ${row.last_name}, ${row.first_name}`);
        encounterEditor.field('bib').set(row.bib)
        encounterEditor.field('first_name').set(row.first_name)
        encounterEditor.field('last_name').set(row.last_name)
        encounterEditor.field('age').set(row.age)
        encounterEditor.field('sex').set(row.sex)
        encounterEditor.field('runner_type').set('yes')
        encounterEditor.buttons('Create')
            .open();
    });
});
