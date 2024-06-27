const dateTimeFormat = 'Y/m/d H:i';
const dateFormat = "mm/dd/yy";
const timepickerOptions = { timeFormat: "H\\:i", show2400: true, listWidth: 1};

// Returns double digit given single number (ex: 1 ==> 01)
const makeDoubleDigit = (num) => {
  return ((num < 10 ? '0' : '') + num);
};

// Takes a date object and returns hh:mm string
// If withSeconds = true, returns hh:mm:ss string
const getTimeString = (options) => {
  const {date, withSeconds} = options;
  let hours = date.getHours();
  let minutes = date.getMinutes();
  let timeString = makeDoubleDigit(hours) + ":" + makeDoubleDigit(minutes);
  if (withSeconds) {
    let seconds = date.getSeconds();
    timeString += ":" + makeDoubleDigit(seconds);
  }
  return timeString;
};

// Takes a date mm/dd/yyy JS date object
const getDateFromString = (dateString) => {
  const [month, day, year] = dateString.split('/').map(Number);
  const newDate = new Date();
  newDate.setYear(year)
  newDate.setMonth(month - 1)
  newDate.setDate(day);
  return newDate;
};

// Takes a date mm/dd/yyy and time HH:mm string and returns JS date object
const getDateFromDateString = (dateString, timeString) => {
  const [month, day, year] = dateString.split('/').map(Number);
  const [hours, minutes] = timeString.split(':').map(Number);
  const newDate = new Date();
  newDate.setYear(year)
  newDate.setMonth(month - 1)
  newDate.setDate(day);
  newDate.setHours(hours)
  newDate.setMinutes(minutes);
  newDate.setSeconds(0);
  return newDate;
};

// Takes a name (e.g. "simulate"), and returns an object of data from the tab's form.
const getDatesFromForm = () => {
  const { startMin, endMax, fullStartDate, fullEndDate } = getApiUserStartEnd();
  let startdatetime = $("#startdate").val() + " " + $("#starttime").val();
  let enddatetime = $("#enddate").val() + " " + $("#endtime").val();

  // Correct start/end dates in case they're out of min/max range
  if (fullStartDate < startMin ) {
    const minDateString = getDateString(startMin);
    const minTimeString = getTimeString({date: startMin, withSeconds: true});
    startdatetime = minDateString + " " + minTimeString;
  }

  if (fullEndDate > endMax) {
    const maxDateString = getDateString(endMax);
    const maxTimeString = getTimeString({date: endMax, withSeconds: true});
    enddatetime = maxDateString + " " + maxTimeString;
  }

  return { startdatetime, enddatetime }
};

// Takes a JS date and returns it in the format mm-dd-yyyy
const getDateString = (date) => {
  let monthNum = date.getMonth() + 1;
  let dayNum = date.getDate();
  if (monthNum < 10) {
    monthNum = `0${monthNum}`;
  }
  if (dayNum < 10) {
    dayNum = `0${dayNum}`;
  }
  return monthNum + "/" + dayNum + "/" + date.getFullYear();
};

// Takes a JS date and returns it in the format MM dd yy (ex: Jan 03 2023)
const getDateStringReadable = (date) => {
  const monthName = date.toLocaleString("default", { month: "short" });
  const day = date.getDate();
  let formattedDay = (day < 10 ? '0' : '') + day;
  return formattedDay + " " + monthName + " " + date.getFullYear();
};

// Takes a start and end date and returns a string representing the timeframe
const getTimeFrameStringReadable = (startDate, endDate) => {
  startDate = new Date(startDate);
  endDate = new Date(endDate);
  const startDateString = getDateStringReadable(startDate) + " " + getTimeString({date: startDate, withSeconds: false});
  const endDateString = getDateStringReadable(endDate) + " " + getTimeString({date: endDate, withSeconds: false});
  return startDateString + " - " + endDateString;
};

// Takes a time string (hh:mm) and returns [hours, minutes] rounded 
// to the nearest 30 minute interval
const roundTimeStringTo30 = (timeString) => {
  let [hours, minutes] = timeString.split(":");
  hours = parseInt(hours);
  minutes = Math.round(minutes / 30) * 30;
  if (minutes === 60) {
    hours++;
    minutes = 0;
  }
  return [hours, minutes];
};

// Takes 2 hour numbers and 2 minute numbers, returns hours2 and minutes2 with a 
// 30 minute space from hours1 and minutes1
const set30MinBetween = (hours1, hours2, minutes1, minutes2, timeConstraint) => {
  hours1 = hours2;
  minutes1 = minutes2;

  // Set this time back or forward 30 minutes to prevent same start & end time
  if (timeConstraint === "maxTime") {
    if (minutes2 === 30) {
      minutes1 = 0;
    }
    if (minutes2 === 0) {
      hours1 -= 1;
      minutes1 = 30;
    }
  }
  if (timeConstraint === "minTime") {
    if (minutes2 === 30) {
      hours1 += 1;
      minutes1 = 0;
    }
    if (minutes2 === 0) {
      minutes1 = 30;
    }
  }

  return [hours1, minutes1];
};

// Takes IDs for date and time inputs and returns a boolean for overlap
const checkForDateTimeOverlap = (thisDateId, otherDateId, thisTimeId, otherTimeId, dateOperator) => {
  const thisDate = $(thisDateId).val();
  const thisTime = $(thisTimeId).val();
  const otherDate = $(otherDateId).val();
  const otherTime = $(otherTimeId).val();
  const thisDateTime = getDateFromDateString(thisDate, thisTime);
  const otherDateTime = getDateFromDateString(otherDate, otherTime);
  return dateOperator === "<" ? thisDateTime >= otherDateTime : thisDateTime <= otherDateTime; 

}

const handleMaxMinTimeChange = (val, otherElId, otherConstraint) => {
  const startDate = $("#startdate").val();
  const endDate = $("#enddate").val();
  if (startDate === endDate) {
    let [thisHours, thisMinutes] = roundTimeStringTo30(val);
    const [otherHours, otherMinutes] = set30MinBetween(thisHours, thisHours, thisMinutes, thisMinutes, otherConstraint);
    $(otherElId).timepicker("option", otherConstraint, otherHours + ":" + otherMinutes);
  }
}

const initTimePicker = (options) => {
  const { elId, otherElId, otherConstraint, maxTime, minTime, defaultTime } = options;
  const thisEl = $(elId);
  thisEl.timepicker({...timepickerOptions, maxTime, minTime});
  thisEl.on("changeTime", (e) => { // Fired by dropdown select only
    handleMaxMinTimeChange(e.target.value, otherElId, otherConstraint);
  });
  thisEl.on("change", (e) => { // Fired by dropdown select + typing
    // Prevent entering > 59 minutes
    let [thisHours, thisMinutes] = e.target.value.split(":").map(v => parseInt(v));
    if (parseInt(thisMinutes) > 59) {
      e.target.value = thisHours + ":" + "59";
    }
  });

  thisEl.on("blur", (e) => {
    let [thisHours, thisMinutes] = e.target.value.split(":").map(v => parseInt(v));
    const startDate = $("#startdate").val();
    const endDate = $("#enddate").val();

    if (startDate === endDate) {
      
      // Prevent entering time that overlaps other time
      const otherTime = $(otherElId).val();
      let [otherHours, otherMinutes] = otherTime.split(":").map(v => parseInt(v));
      let thisTotalMinutes = (thisHours * 60) + thisMinutes;
      let otherTotalMinutes = (otherHours * 60) + otherMinutes;
      let alertMessage = "";
      
      if (otherConstraint === "minTime") {
        if (thisTotalMinutes >= otherTotalMinutes) {
          thisTotalMinutes = otherTotalMinutes - 30;
          alertMessage = "Start date must come before end date.";
        }
      }

      if (otherConstraint === "maxTime") {
        if (thisTotalMinutes <= otherTotalMinutes) {
          thisTotalMinutes = otherTotalMinutes + 30;
          alertMessage = "End date must come after start date."
        }
      }

      if (alertMessage) {
        alert(alertMessage);
        // Correct this time and other constraint
        const correctedHours = String(Math.floor(thisTotalMinutes / 60)).padStart(2, "0"); 
        const correctedMinutes = String(thisTotalMinutes % 60).padStart(2, "0"); 
        e.target.value = correctedHours + ":" + correctedMinutes;
        [otherHours, otherMinutes] = roundTimeStringTo30(otherTime);
        $(otherElId).timepicker("option", otherConstraint, otherHours + ":" + otherMinutes);    
      }
    
    }
  })

  thisEl.val(defaultTime)
};

const initDatePicker = (options) => {
  const { 
    elId, 
    otherDateElId, 
    thisTimeId, 
    otherTimeId, 
    minDate, 
    maxDate, 
    defaultDate,
    defaultDateConstraint,
    otherDateConstraint,
    thisTimeConstraint,
    otherTimeConstraint,
    otherTimeDefaultVal,
    thisTimeDefaultVal,
    dateOperator
  } = options;
  
  // Destroy old datepicker instance
  if ($(elId).datepicker("option", "defaultDate")) {
    $(elId).datepicker("destroy");
  }

  $(elId).datepicker({
    altFormat: dateFormat,
    minDate, maxDate,
    defaultDate,
    constrainInput: true,
    onSelect: (newDate) => {
      if (typeof newDate !== "string") {
        newDate = getDateString(newDate)
      }
      const thisTimeEl = $(thisTimeId);
      const otherTimeEl = $(otherTimeId);
      const otherDateEl = $(otherDateElId);
      const otherDate = otherDateEl.val();
      const thisTime = thisTimeEl.val();
      
      // If selected date lands on other date
      if (newDate === otherDate) {
        const otherTime = otherTimeEl.val();
        let thisTime = thisTimeEl.val();
        const isOverlapping = checkForDateTimeOverlap(elId, otherDateElId, thisTimeId, otherTimeId, dateOperator);
        let [thisHours, thisMinutes] = roundTimeStringTo30(thisTime);
        let [otherHours, otherMinutes] = roundTimeStringTo30(otherTime);
        const [updatedHours, updatedMinutes] = set30MinBetween(thisHours, otherHours, thisMinutes, otherMinutes, thisTimeConstraint);

        // Auto set this date if it overlaps other date
        if (isOverlapping) {
          thisTimeEl.timepicker("setTime", updatedHours + ":" + updatedMinutes);
        } 

        otherTimeEl.timepicker("option", otherTimeConstraint, otherHours + ":" + otherMinutes);
        thisTimeEl.timepicker("option", thisTimeConstraint, updatedHours + ":" + updatedMinutes);

      }

      // selected date not on other date
      if (otherDate !== newDate) {
        // Reset end minTime
        otherTimeEl.timepicker("option", otherTimeConstraint, otherTimeDefaultVal);
        thisTimeEl.timepicker("option", thisTimeConstraint, thisTimeDefaultVal);
      }

      // selected date not on default constraint
      if (newDate !== defaultDateConstraint) {
        thisTimeEl.timepicker("option", otherTimeConstraint, otherTimeDefaultVal);
      }

      // selected date lands on default constraint
      if (newDate === defaultDateConstraint) {
        const newTimeConstraint = getTimeString({date: dateOperator === "<" ? minDate : maxDate, withSeconds: false});
        thisTimeEl.timepicker("option", otherTimeConstraint, newTimeConstraint);
        const selectedDateTime = getDateFromDateString(newDate, thisTime);
        const isOverlapping = dateOperator === "<" ? selectedDateTime < minDate : selectedDateTime > maxDate; 
        
        // selected date overlaps default constraint
        if (isOverlapping) {
          thisTimeEl.timepicker("setTime", newTimeConstraint);
        }
      }

      otherDateEl.datepicker('option', otherDateConstraint, newDate);

    }

  });

};

const setDateInputsValid = (dateInputElId, timeInputElId, feedbackElId) => {
  $(dateInputElId).removeClass("is-invalid");
  $(timeInputElId).removeClass("is-invalid");
  $(feedbackElId).hide();
};

const setDateInputsInvalid = (dateInputElId, timeInputElId, feedbackElId) => {
  $(dateInputElId).addClass("is-invalid");
  $(timeInputElId).addClass("is-invalid");
  $(feedbackElId).show();
};

// Checks for a valid date in the format "mm/dd/yyyy", returns true/false
const validateDate = (dateString) => {
  try {
    $.datepicker.parseDate(dateFormat, dateString);
    return true;
  } catch (e) { return false; }
}

// Validate single date input
const validateDateInput = (dateElId, timeElId, feedbackElId) => {
  const dateString = $(dateElId).val();
  const isValid = validateDate(dateString);
  if (isValid) {
    setDateInputsValid(dateElId, timeElId, feedbackElId);
  }
  else {
    setDateInputsInvalid(dateElId, timeElId, feedbackElId);
  }
  return isValid;
};

// Gets and returns start/end dates strings, min/max, and full start/end dates
const getApiUserStartEnd = () => {
  const startDateString = $("#startdate").val();
  const endDateString = $("#enddate").val();
  const startTimeString = $("#starttime").val();
  const endTimeString = $("#endtime").val();
  return ({
    startDateString,
    endDateString,
    startMin: new Date($("#startdate").datepicker("option", "minDate")),
    endMax: new Date($("#enddate").datepicker("option", "maxDate")),
    fullStartDate: getDateFromDateString(startDateString, startTimeString),
    fullEndDate: getDateFromDateString(endDateString, endTimeString)
  })
};

// Validate start and end date + time inputs
const validateDateTimeInputs = () => {
  const { 
    startDateString, 
    endDateString, 
    startMin, 
    endMax, 
    fullStartDate, 
    fullEndDate 
  } = getApiUserStartEnd();
  let startDateIsValid = validateDate(startDateString);
  let endDateIsValid = validateDate(endDateString);
  let isValid = true;

  // Set seconds and milliseconds to zero for accurate comparison
  fullStartDate.setSeconds(0);
  fullEndDate.setSeconds(0);
  fullStartDate.setMilliseconds(0);
  fullEndDate.setMilliseconds(0);
  startMin.setSeconds(0);
  endMax.setSeconds(0);
  startMin.setMilliseconds(0);
  endMax.setMilliseconds(0);

  const startMinTime = startMin.getTime();
  const endMaxTime = endMax.getTime();
  const startTime = fullStartDate.getTime();
  const endTime = fullEndDate.getTime();

  if (startTime < startMinTime || startTime >= endTime || !startDateIsValid) {
    setDateInputsInvalid("#startdate", "#starttime", "#startdate-feedback");
    isValid = false;
  }

  else {
    setDateInputsValid("#startdate", "#starttime", "#startdate-feedback");
  }

  if (endTime > endMaxTime || endTime <= startTime || !endDateIsValid) {
    setDateInputsInvalid("#enddate", "#endtime", "#enddate-feedback");
    isValid = false;
  }

  else {
    setDateInputsValid("#enddate", "#endtime", "#enddate-feedback");
  }

  return isValid;

};