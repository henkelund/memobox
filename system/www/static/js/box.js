(function (exports, ng, $) {
    'use strict';

    /**
     * @var Object box
     */
    var box = ng.module('box', ['ngResource', 'ui.router', 'infinite-scroll', 'ngSanitize']);
    exports.box = box;
	
	/* Repeat directive that activates tooltip  on loaded devices for device info on mouseover*/
	box.directive('deviceRepeatDirective', function ($timeout) {
        return {
            restrict: 'A',
            link: function (scope, element, attr) {
                if (scope.$last === true) {
                    $timeout(function () {
                        scope.$emit('deviceRepeatDirective');
                        if (!window.matchMedia || (window.matchMedia("(min-width: 767px)").matches)) {
	                        //$(".device").on('click',function(){$(this).tooltip('destroy');});
	                        $(".device").tooltip();
                        }
                    });
                }
            }
        }
     });
	
	// Infinity constructor function to encapsulate HTTP and pagination logic
	box.factory('Infinity', function($http) {
	  var Infinity = function($scope) {
	  	this.me = $scope;
	    this.images = [];
	    this.busy = false;
	    this.after = 1;
	    this.viewMonth = null;
	    this.viewYear = null; 
		this.monthArr = "Alert";
		this.device = -1; 
		this.type = null;
		this.imageCount = -1; 
	};

	  // Todo, move this from infinity to device 
	  Infinity.prototype.editDevice = function(device) {
		  $('#deviceDetailModal').attr("device", device);					  
		  $.ajax({
			    url : "/device/detail?id="+device,
				async: false,
				context: this,
			    success : function(result){
			        $("#deviceDetailModalInput").attr("value", result.product_name);
			        $('#deviceDetailModal').modal('show');				
			    }
		  });	  	
	  }

	  // Todo, move this from infinity to device 
	  Infinity.prototype.updateDevice = function() {
		$.ajax({
		    url : "/device/update?id="+$('#deviceDetailModal').attr("device")+"&product_name="+$("#deviceDetailModalInput").val(),
			async: false,
			context: this,
		    success : function(result){
		        window.location = "/"; 
		    }
		});	  	
	  }

	  // Todo, move this from infinity to device 	  
	  Infinity.prototype.showPicture = function(file) {
		$.ajax({
		    url : "/files/details?id="+file,
			async: false,
			context: this,
		    success : function(result){
				var ts = new Date(null);
				ts.setTime(result.created_at*1000);
				
				var time = new Date(result.created_at*1000);
				var viewMonth = time.getMonth();
				var viewYear = time.getFullYear().toString();
				var viewDate = time.getDate();
				var month = Array("January","February","March","April","May","June","July","August","September","October","November","December");
				
				$("#filesDetailModalLabel").html(result.name+" – "+viewDate +" "+ month[viewMonth] + ", "+viewYear+" – "+result.product_name);
				$("#filesDetailModalLabel").attr("file", file);
				
				if(result.type == "video") {
					$("#moddalVideoContainer").html('<video id="modalVideo" style="display: none;" width="100%" height="520" controls="controls" autoplay="autoplay"><source id="modalSource" src="" type="video/mp4" /></video>');
					
					if(isLocal) {
						$("#modalVideo > source").attr("src", result.abspath.replace("/backupbox/data/devices/", "/static/devices/")+"/"+result.name);
					} else {
						$("#modalVideo > source").attr("src", result.abspath.replace("/backupbox/data/devices/", "/backups/" + username + "/devices/")+"/"+result.name);
					}
					
					$("#originalImage").attr("src", result.abspath.replace("/backupbox/data/devices/", "/backups/" + username + "/devices/")+"/"+result.name);
					$("#modalVideo").load();
					$("#modalVideo").show();
					$("#modalImage").hide();
				} else {
					$("#modalVideo").hide();
					$("#modalImage").show();
					$("#modalDownload").attr("href", "/files/stream/"+result._id+"/"+result.name+"/full/0");
					//document.getElementById("modalDownload").href 
					$("#originalImage").attr("src", "/files/stream/"+result._id+"/"+result.name+"/full/0");
					$("#modalImage").attr("src", "/files/stream/"+result._id+"/"+result.name+"/thumbnail/520");
				}
		
		        $('#filesDetailModal').modal('show');				
		    }
		});	  	
  	
	  	//var f = new FileService();
	  	//f.loadDetails(file);	  	
	  }
	  
	  /**
	  * Method that loads next page in the infinite scroll. Device ID and File type ID can be passed as filtering parameters. 
	  *	  
	  **/
	  Infinity.prototype.nextPage = function(_device, _type) {
	    // Make sure previous request is not running
	    if (this.busy) return;
	    
	    // Flag this method as running
	    this.busy = true;	
	    
	    // Parameter to determine wether content was replaced or appended. replace => chnageState = true
	    var changedState = false; 
		
		// If a device ID was passed, let's filter on device
		if(_device != null) {
			if(this.device != _device) {
				changedState = true;
				this.after = 1; 
				$(".device span").removeClass("label label-success");
				$("#"+_device+" span").addClass("label label-success");
				this.device = _device; 
			} else {
				this.device = -1; 
				$(".device span").removeClass("label label-success");
				this.after = 1; 
				changedState = true; 
			}
			

			/*
			Not used script that is supposed to list all available months of device
			$.ajax({
			    url : "/files/calendar?device="+_device,
				async: false,
				context: this,
			    success : function(result){
					//alert(JSON.stringify(result));
			    }
			});*/
		}
		
		// If a file type(Videos or Images) was added, Let's filter on type
		if(_type != null) {
			if(this.type != _type) {
				changedState = true;
				this.after = 1; 
				$(".type").removeClass("selectedDevice");
				$("#type-"+_type).addClass("selectedDevice");
				this.type = _type; 				
			} else {
				changedState = true;
				this.after = 1; 
				$(".type").removeClass("selectedDevice");
				this.type = null;
			}
		}
		
		// Clear visiable area of old images if the state was changed
		if(changedState == true) {
			this.me.items = [];
		}
	
		// Lead request
		$.ajax({
		    url : "/files?after="+this.after+"&device="+this.device+"&format="+this.type,
			async: false,
			context: this,
		    success : function(result){
		    	if(changedState == true) {
					if (!window.matchMedia || (window.matchMedia("(max-width: 767px)").matches)) {
						$("#mainNav").css("height", "0px");
						$("#mainNav").removeClass("in");
						$("#mainNav-btn").addClass("collapsed");
					}
				}

				// If response resulted in no images, show error message
				if(result.files.length == 0 && this.me.items.length == 0) {
					this.me.missingImages = true; 	
				} else {
					this.me.missingImages = false; 
				}
				
				// Loop JSON response and add images to ng-repeat array
			    for(var i = 0; i < result.files.length; i++) {
			      var type_content = ""; 
			      
			      // If current item is a video, add info about lenght in thumbnail. 
			      if(result.files[i].type == "video" && result.files[i].value != null) {
			      	  var video_length = result.files[i].value.split(" ")
			      	  var suffix = "ms"; 
			      	  
			      	  for (var ind = 0; ind < video_length.length; ++ind) {
			      	  	if(video_length[ind].indexOf(suffix, video_length[ind].length - suffix.length) == -1)
							type_content += video_length[ind].replace("mn", "min")+" ";
					  }
			      }		
			      
			      // Push thumbnail item to ng-repeat array	      
			      this.me.items.push({background:result.files[i].thumbnail, id:result.files[i].file, created_at:result.files[i].created_at, type:result.files[i].type, type_content:type_content});
			    }			    
				
				// Increase current page number(for next request)
		        this.after = this.after + 1;
		        this.busy = false;		        
		    }
		});
	  };
	
	  return Infinity;
	});	

    /**
     * Configure the box app
     */
    box.config(function ($stateProvider, $urlRouterProvider) {

        $urlRouterProvider.otherwise('/');
		
		// When the application starts we are lading device list and first page of the result. 
        $stateProvider
            .state('devices', {
                url: '/devices',
                controller: 'DevicesCtrl',
                templateUrl: '/templates/devices.html'
            })
            .state('files', {
                url: '/',
                controller: 'FilesCtrl',
                templateUrl: '/templates/files.html'
            })
    });

    /**
     * Run the box app
     */
    box.run(function ($window) {
        ng.element($window).bind('scroll', function () {
        	// If the appliaction is running on a desktop computer, add fancy paralax scroll to images
            if (window.matchMedia && (window.matchMedia("(min-width: 1025px)").matches)) {
	            var winHeight = $($window).height();
	            $('.preview.image').each(function () {
	                var rect = this.getBoundingClientRect(),
	                    el = $(this),
	                    pos,
	                    percent;
	                if (rect.bottom >= 0 && rect.top <= winHeight) {
	                    pos = rect.top / (winHeight - el.height());
	                    percent = Math.round(Math.min(100, Math.max(0,
	                                pos * 100)));
	                    el.css('backgroundPosition', '50% ' + percent + '%');
	                }
	            });
			}
        });
    });

    /**
     * File service
     */
    box.factory('FileService', function ($resource, $window, $q) {

        /**
         *
         */
        var FileService = function () {
            this.filesResource = $resource('/files');
            this.filterResource = $resource('/files/filters');
            this.detailsResource = $resource('/files/details');
            this.deviceResource = $resource('/devices');
            this.calendarResource = $resource('/files/calendar');
            this.calendar = [];
            this.devices = [];
            this.missingDevices = false; 
            this.files = [];
            this.filters = [];
            this.details = [];
        };
        FileService.prototype = {

            /**
             * Successful files load callback
             */
            loadFilesSuccess: function (resource) {
                this.files = resource.files;
                //console.log(resource.sql);
            },

            /**
             * Successful filters load callback
             */
            loadFiltersSuccess: function (data) {
                this.filters = data.filters;
            },

            /**
             * Successful filters load callback
             */
            loadCalendarSuccess: function (data) {
                this.calendar = data;
            },

            /**
             * Successful filters load callback
             */
            loadDevicesSuccess: function (data) {
                this.devices = data.devices;
                if(this.devices.length == 0) {
	                this.missingDevices = true; 
                }
            },


            /**
             * Successful filters load callback
             */
            loadDetailsSuccess: function (data) {
                if (data['_id'] !== undefined) {
                    this.details[data['_id']] = data;
                }
            },

            /**
             * Failed load callback
             */
            loadError: function (data) {
                //console.log(data);
            },

            /**
             * Load files passing 'filter'
             */
            loadFiles: function (filter, complete) {
                var that = this,
                    args = {}, // arguments
                    fk;        // filter key

                if ($window.devicePixelRatio && $window.devicePixelRatio > 1) {
                    args.retina = 1;
                }

                if (typeof filter === 'object') {
                    for (fk in filter) {
                        if (filter.hasOwnProperty(fk) && filter[fk].length) {
                            args[fk] = filter[fk].join(',');
                        }
                    }
                }

                this.filesResource.get(
                    args,
                    function (data) {
                        that.loadFilesSuccess(data);
                        if (typeof complete === 'function') {
                            complete(data);
                        }
                    },
                    function (data) {
                        that.loadError(data);
                        if (typeof complete === 'function') {
                            complete(data);
                        }
                    }
                );
                return this;
            },


            /**
             * Load available calendar
             */
            loadCalendar: function () {
                this.calendarResource.get(
                    {},
                    this.loadCalendarSuccess.bind(this),
                    this.loadError.bind(this)
                );
                return this;
            },

            /**
             * Load available devices
             */
            loadDevices: function () {
                this.deviceResource.get(
                    {},
                    this.loadDevicesSuccess.bind(this),
                    this.loadError.bind(this)
                );
                return this;
            },
            
            /**
             * Load available filters
             */
            loadFilters: function () {
                this.filterResource.get(
                    {},
                    this.loadFiltersSuccess.bind(this),
                    this.loadError.bind(this)
                );
                return this;
            },

            /**
             * Load file by id
             */
            loadDetails: function (id) {
                var that = this,
                    deferred = $q.defer(),
                    resource;

                if (this.details[id] !== undefined) {
                    deferred.resolve();
                } else {
                    resource = this.detailsResource.get(
                        {id: id},
                        function (data) {
                            that.loadDetailsSuccess(data);
                            deferred.resolve();
                        },
                        function (data) {
                            that.loadError(data);
                            deferred.resolve();
                        }
                    );
                }

                return deferred.promise;
            },

            /**
             * Get laoded details
             */
            getDetails: function (id) {
                return this.details[id] || false;
            }
        };

        return new FileService();
    });

    /**
     * Files controller
     */
    box.controller('FilesCtrl', function ($scope, $location, FileService, Infinity) {

        var that = this;
        this.fileService = FileService.loadFiles().loadDevices();
        $scope.infinity = new Infinity($scope);
        $scope.items = [];
        $scope.render = function(e) {
			return $(e).html();
        }
        
        this.filterState = {};
        this.isFilterPending = false;
        $('#filesDetailModal').modal({show: false})
                .on('hide.bs.modal', function () {
            $location.path('/');
            $scope.$apply();
        });

        $scope.FilesCtrl = this;
        return this;
    });

}(window, angular, jQuery || {log: function () { 'use strict'; return; }}));